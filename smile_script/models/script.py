# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from StringIO import StringIO
import time

from openerp import api, fields, models, sql_db, SUPERUSER_ID, tools
from openerp.exceptions import UserError
from openerp.modules.registry import Registry
from openerp.osv import osv, orm
from openerp.tools import convert_xml_import
from openerp.tools.translate import _

from openerp.addons.smile_log.tools import SmileDBLogger

_logger = logging.getLogger(__name__)


def _get_exception_message(exception):
    msg = isinstance(exception, (osv.except_osv, orm.except_orm)) and exception.value or exception
    return tools.ustr(msg)


class SmileScript(models.Model):
    _name = 'smile.script'
    _description = 'Smile Script'

    create_date = fields.Datetime('Created on', required=False, readonly=True)
    create_uid = fields.Many2one('res.users', 'Created by', required=False, readonly=True)
    validation_date = fields.Datetime('Validated on', readonly=True)
    validation_user_id = fields.Many2one('res.users', 'Validated by', readonly=True)
    name = fields.Char(size=128, required=True, readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(required=True, readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('python', 'Python'), ('sql', 'SQL'), ('xml', 'XML')], 'Type', required=True, readonly=True,
                            states={'draft': [('readonly', False)]})
    code = fields.Text(required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], required=True, readonly=True, default='draft')
    intervention_ids = fields.One2many('smile.script.intervention', 'script_id', 'Interventions', readonly=True)
    expect_result = fields.Boolean('Expect a result')

    @api.multi
    def _get_validated_scripts(self):
        validated_scripts = []
        for script in self:
            if script.state != 'draft':
                validated_scripts.append(script)
        return validated_scripts

    @staticmethod
    def _can_write_after_validation(vals):
        keys = vals and vals.keys() or []
        for field in keys:
            if field not in ['name']:
                return False
        return True

    @api.multi
    def write(self, vals):
        if not vals:
            return True
        if self._get_validated_scripts() and not SmileScript._can_write_after_validation(vals):
            raise UserError(_('You can only modify draft scripts!'))
        return super(SmileScript, self).write(vals)

    @api.multi
    def unlink(self):
        validated_scripts = self._get_validated_scripts()
        if validated_scripts:
            raise UserError(_('You can only delete draft scripts!'))
        intervention_ids = []
        for script in self.read(['intervention_ids']):
            intervention_ids.extend(script['intervention_ids'])
        if intervention_ids:
            self.env['smile.script.intervention'].browse(intervention_ids).unlink()
        return super(SmileScript, self).unlink()

    def copy_data(self, cr, uid, script_id, default=None, context=None):
        default = default.copy() if default else {}
        default.update({'state': 'draft', 'intervention_ids': []})
        return super(SmileScript, self).copy_data(cr, uid, script_id, default, context)

    @api.multi
    def validate(self):
        validated_scripts = self._get_validated_scripts()
        if validated_scripts:
            raise UserError(_('You can only validate draft scripts!'))
        return self.write({'state': 'validated', 'validation_user_id': self._uid,
                           'validation_date': time.strftime('%Y-%m-%d %H:%M:%S')})

    @api.multi
    def _run(self, logger):
        if self.type == 'sql':
            return self._run_sql()
        elif self.type == 'xml':
            return self._run_xml()
        elif self.type == 'python':
            return self._run_python(logger)
        raise NotImplementedError(self.type)

    @api.one
    def run(self):
        cr, uid, context = self.env.args
        intervention_obj = self.env['smile.script.intervention']
        if not self._context.get('test_mode'):
            if self.state != 'validated':
                raise UserError(_('You can only run validated scripts!'))
        intervention = intervention_obj.create({'script_id': self.id, 'test_mode': context.get('test_mode')})
        logger = SmileDBLogger(cr.dbname, 'smile.script.intervention', intervention.id, uid)
        if not context.get('do_not_use_new_cursor'):
            intervention_cr = sql_db.db_connect(cr.dbname).cursor()
        else:
            intervention_cr = cr
        intervention_vals = {}
        try:
            _logger.info('Running script: %s\nCode:\n%s' % (self.name.encode('utf-8'), self.code.encode('utf-8')))
            result = self.with_env(self.env(cr=intervention_cr))._run(logger)
            if not context.get('do_not_use_new_cursor') and context.get('test_mode'):
                logger.info('TEST MODE: Script rollbacking')
                intervention_cr.rollback()
            elif not context.get('do_not_use_new_cursor'):
                intervention_cr.commit()
            intervention_vals.update({'state': 'done', 'result': result})
            _logger.info('Script execution SUCCEEDED: %s\n' % (self.name.encode('utf-8'),))
        except Exception, e:
            intervention_vals.update({'state': 'exception', 'result': _get_exception_message(e)})
            _logger.error('Script execution FAILED: %s\nError:\n%s' % (self.name.encode('utf-8'), _get_exception_message(e).encode('utf-8')))
        finally:
            if not context.get('do_not_use_new_cursor'):
                intervention_cr.close()
        intervention_vals.update({'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return intervention.write(intervention_vals)

    @api.multi
    def run_test(self):
        return self.with_context(test_mode=True).run()

    @api.multi
    def _run_python(self, logger):
        self.ensure_one()
        localdict = {
            'self': self,
            'logger': logger,
            'time': time,
            'tools': tools,
        }
        exec self.code in localdict
        return localdict['result'] if 'result' in localdict else 'No expected result'

    @api.multi
    def _run_sql(self):
        self.ensure_one()
        self._cr.execute(self.code)
        if self.expect_result:
            return tools.ustr(self._cr.fetchall())
        return 'No expected result'

    @api.multi
    def _run_xml(self):
        self.ensure_one()
        convert_xml_import(self._cr, __package__, StringIO(self.code.encode('utf-8')))
        return 'No expected result'


STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]


def state_cleaner(method):
    def wrapper(self, cr, *args, **kwargs):
        res = method(self, cr, *args, **kwargs)
        if self.get('smile.script.intervention'):
            cr.execute("select relname from pg_class where relname='smile_script_intervention'")
            if cr.rowcount:
                export_ids = self.get('smile.script.intervention').search(cr, SUPERUSER_ID, [('state', '=', 'running')])
                if export_ids:
                    self.get('smile.script.intervention').write(cr, SUPERUSER_ID, export_ids, {'state': 'exception'})
        return res
    return wrapper


class SmileScriptIntervention(models.Model):
    _name = 'smile.script.intervention'
    _description = 'Smile Script Intervention'
    _rec_name = 'create_date'
    _order = 'create_date DESC'

    def __init__(self, pool, cr):
        super(SmileScriptIntervention, self).__init__(pool, cr)
        if not getattr(Registry, '_intervention_state_cleaner', False):
            setattr(Registry, 'setup_models', state_cleaner(getattr(Registry, 'setup_models')))
        else:
            Registry._intervention_state_cleaner = True

    create_date = fields.Datetime('Intervention start', required=True, readonly=True)
    end_date = fields.Datetime('Intervention end', readonly=True)
    create_uid = fields.Many2one('res.users', 'User', required=True, readonly=True)
    script_id = fields.Many2one('smile.script', 'Script', required=True, readonly=True)
    state = fields.Selection(STATES, readonly=True, required=True, default='running')
    test_mode = fields.Boolean('Test Mode', readonly=True)
    result = fields.Text(readonly=True)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs',
                              domain=[('model_name', '=', 'smile.script.intervention')], readonly=True)

    @api.multi
    def unlink(self):
        for intervention in self:
            if not intervention.test_mode:
                raise UserError(_('Intervention cannot be deleted'))
        return super(SmileScriptIntervention, self).unlink()

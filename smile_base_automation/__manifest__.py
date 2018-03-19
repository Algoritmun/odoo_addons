# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Automated Actions",
    "version": "0.1",
    "depends": [
        "base_automation",
        "smile_log",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module extends base_automation.

Additional features

    * Extend automated actions to:
        * Trigger on other method
        * Limit executions per record
        * Log executions for actions not on timed condition
        * Raise customized exceptions
        * Categorize them
    * Extend server actions to:
        * Force execution even if records list is empty
        * Execute in asynchronous mode

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/ir_actions.xml",
        "views/ir_model_methods_view.xml",
        "views/base_automation_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}

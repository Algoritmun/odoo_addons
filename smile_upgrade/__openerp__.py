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

{
    "name": "Smile Upgrade",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "description": """Smile Upgrade

Objectives

    * Allow to upgrade automatically database after code update and server restarting
    * Display a maintenance page instead of home page and kill XML/RPC services during upgrades

Execution

    su openerp -c "openerp-server -c rcfile -d db_name --load=web,smile_upgrade"

Configuration

    * Upgrades structure
        <project_directory>
        `-- upgrades
            |-- 1.1
            |   |-- __init__.py
            |   |-- __upgrade__.py
            |   |-- *.sql
            |   `-- *.yml                   # only for post-load
            |-- 1.2
            |   |-- __init__.py
            |   |-- __upgrade__.py
            |   `-- *.sql
            `-- upgrade.conf

    * Upgrades configuration -- upgrade.conf
        [options]
        version=1.2

    * Upgrade configuration -- __upgrade__.py
        Content: dictonary with the following keys:
            * version
            * databases: let's empty if valid for all databases
            * description
            * modules_to_upgrade: modules list to update or install
            * pre-load: list of .sql files
            * post-load: list with .sql and .yml files

    * OpenERP server configuration -- rcfile=~/.openerp_serverrc
        [options]
        upgrades_path = <project_directory>
        stop_after_upgrades = True if you want to stop server after upgrades else False

Additional features

    * In post-load, you can replace filename string by tuple
      (filename, 'rollback_and_continue' or 'not_rollback_and_continue' or 'raise') -- default value = 'raise'
    * In .yml files, add context['store_in_secure_mode'] = True
      if you want to compute fields.function (_store_set_values)
      by catching errors and logging them {record_id: error}

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "init_xml": [],
    "update_xml": [],
    'demo_xml': [],
    'test': [],
    "auto_install": True,
    "installable": True,
    "application": False,
}

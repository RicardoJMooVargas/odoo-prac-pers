# -*- coding: utf-8 -*-
import mimetypes

# Fix para el error 500 al cargar iconos/fuentes en Odoo sobre Windows
mimetypes.add_type('application/font-woff', '.woff')
mimetypes.add_type('application/font-woff2', '.woff2')

from . import models
from . import wizard

-- Datos de ejemplo para probar el panel con Supabase conectado.
insert into public.actores (nombre, tipo, sector, contacto) values
  ('Grupo de Investigación en Energía', 'universidad', 'Academia',     'energia@ejemplo.edu.co'),
  ('Secretaría de Planeación Municipal','estado',      'Gobierno local','planeacion@ejemplo.gov.co'),
  ('Asociación de Productores del Valle','comunidad',  'Agro',          'asoproductores@ejemplo.org'),
  ('Fundación Salud para Todos',        'ong',         'Tercer sector', 'contacto@ejemplo.org'),
  ('Industrias del Norte S.A.S.',       'empresa',     'Manufactura',   'innovacion@ejemplo.com')
on conflict do nothing;

insert into public.proyectos (titulo, resumen, descripcion, area, estado, avance, presupuesto, lider, equipo, etiquetas, fecha_inicio, fecha_fin) values
  ('Riego inteligente para cultivos de cebolla',
   'Red de sensores de humedad y control automático de riego para pequeños productores.',
   'Prototipo de nodos IoT de bajo costo con piloto en tres fincas y guía de instalación replicable.',
   'Agroindustria', 'ejecucion', 62, 28500000, 'Laura Sepúlveda',
   '{"Laura Sepúlveda","Andrés Quintero","Nicolás Pabón"}', '{"IoT","agua","sensores"}', '2026-02-10', '2026-11-30'),
  ('Observatorio de calidad del aire urbano',
   'Estaciones comunitarias de medición de material particulado con tablero público.',
   'Ocho estaciones de bajo costo validadas contra una estación de referencia, con alertas por umbrales.',
   'Ambiente', 'ejecucion', 45, 41000000, 'Diego Ramírez',
   '{"Diego Ramírez","Sara Ortega"}', '{"aire","datos abiertos","salud pública"}', '2026-01-20', '2027-01-20'),
  ('Microrred solar para sede rural',
   'Sistema fotovoltaico con almacenamiento y monitoreo de consumo.',
   'Microrred de 12 kWp con tablero de generación y consumo en tiempo real.',
   'Energía', 'finalizado', 100, 86000000, 'Óscar Peñaranda',
   '{"Óscar Peñaranda","Valeria Rincón","Hugo Meza"}', '{"solar","eficiencia","monitoreo"}', '2025-03-01', '2026-02-28')
on conflict do nothing;

insert into public.oportunidades (titulo, entidad, tipo, monto, cierra_en, areas, url) values
  ('Convocatoria de ciencia aplicada 2026', 'Ministerio de Ciencia', 'convocatoria', 300000000, '2026-10-15', '{"Tecnología","Ambiente","Energía"}', 'https://ejemplo.gov.co/convocatoria'),
  ('Fondo de innovación agroindustrial',    'Cámara de Comercio',    'financiacion', 120000000, '2026-09-30', '{"Agroindustria"}',                     'https://ejemplo.org/fondo'),
  ('Mentoría en transferencia tecnológica', 'Red de Oficinas TT',    'mentoria',     null,      '2026-11-20', '{"Tecnología","Salud"}',                'https://ejemplo.org/mentoria')
on conflict do nothing;

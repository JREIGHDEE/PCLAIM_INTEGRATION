/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Davao City addresses (PSGC names)

   The clinic is in Cabantian, Davao City, and so is almost every
   patient, so the lists are Davao City's own: its 182 barangays, and
   the subdivisions the staff see most. Anything else - a patient from
   another city or province - is typed into the box that appears when
   "Not on the list" is chosen, so nothing is shut out.

   Kept here rather than fetched: the clinic works without the internet,
   and a list that only loads when the line is up is a list that fails
   on the day it is needed.

   Barangay names follow the Philippine Standard Geographic Code. The
   numbered ones are the Poblacion District and are written the way the
   form writes them - "19-B", not "Barangay 19-B" - so the box holds the
   name and nothing else.
═══════════════════════════════════════════════════════════ */

/* The 40 numbered Poblacion barangays, in order. */
window.PH_POBLACION = [
  '1-A', '2-A', '3-A', '4-A', '5-A', '6-A', '7-A', '8-A', '9-A', '10-A',
  '11-B', '12-B', '13-B', '14-B', '15-B', '16-B', '17-B', '18-B', '19-B', '20-B',
  '21-C', '22-C', '23-C', '24-C', '25-C', '26-C', '27-C', '28-C', '29-C', '30-C',
  '31-D', '32-D', '33-D', '34-D', '35-D', '36-D', '37-D', '38-D', '39-D', '40-D'
];

/* The named barangays of the city's eleven administrative districts. */
window.PH_NAMED_BARANGAYS = [
  'Acacia', 'Agdao Proper', 'Alambre', 'Alejandra Navarro (Lasang)', 'Alfonso Angliongto Sr.',
  'Angalan', 'Atan-Awe', 'Baganihan', 'Bago Aplaya', 'Bago Gallera', 'Bago Oshiro',
  'Baguio Proper', 'Balengaeng', 'Baliok', 'Bangkas Heights', 'Bantol', 'Baracatan',
  'Bato', 'Bayabas', 'Biao Escuela', 'Biao Guianga', 'Biao Joaquin',
  'Binugao', 'Bucana', 'Buda', 'Buhangin Proper', 'Bunawan Proper', 'Cabantian',
  'Cadalian', 'Calinan Proper', 'Callawa', 'Camansi', 'Carmen', 'Catalunan Grande',
  'Catalunan Pequeño', 'Catigan', 'Cawayan', 'Centro (San Juan)', 'Colosas', 'Communal',
  'Crossing Bayabas', 'Dacudao', 'Dalag', 'Dalagdag', 'Daliao', 'Daliaon Plantation',
  'Datu Salumay', 'Dominga', 'Dumoy', 'Eden', 'Fatima (Benowang)', 'Gatungan',
  'Gumalang', 'Gumitan', 'Ilang', 'Inayangan', 'Indangan', 'Kap. Tomas Monteverde Sr.',
  'Kilate', 'Lacson', 'Lamanan', 'Lampianao', 'Langub', 'Lizada', 'Los Amigos',
  'Lubogan', 'Lumiad', 'Ma-a', 'Mabuhay', 'Magsaysay', 'Mahayag', 'Malabog',
  'Malagos', 'Malamba', 'Manambulan', 'Mandug', 'Manuel Guianga', 'Mapula',
  'Marapangi', 'Marilog Proper', 'Matina Aplaya', 'Matina Biao', 'Matina Crossing',
  'Matina Pangi', 'Megkawayan', 'Mintal', 'Mudiang', 'Mulig', 'New Carmen',
  'New Valencia', 'Pampanga', 'Panacan', 'Panalum', 'Pandaitan', 'Pangyan',
  'Paquibato Proper', 'Paradise Embak', 'Rafael Castillo', 'Riverside', 'Salapawan',
  'Salaysay', 'Saloy', 'San Antonio', 'San Isidro (Licanan)', 'Santo Niño', 'Sasa',
  'Sibulan', 'Sirawan', 'Sirib', 'Suawan (Tuli)', 'Subasta', 'Sumimao', 'Tacunan',
  'Tagakpan', 'Tagluno', 'Tagurano', 'Talandang', 'Talomo Proper', 'Talomo River',
  'Tamayong', 'Tambobong', 'Tamugan', 'Tapak', 'Tawan-Tawan', 'Tibuloy', 'Tibungco',
  'Tigatto', 'Toril Proper', 'Tugbok Proper', 'Tungakalan', 'Ula', 'Vicente Hizon Sr.',
  'Waan', 'Wangan', 'Wines',
  'Leon Garcia Sr.', 'Lapu-Lapu'
];

/* Province -> city -> barangays. One city: see the note above. */
window.PH_ADDRESS = {
  'Davao del Sur': {
    'Davao City': window.PH_POBLACION.concat(window.PH_NAMED_BARANGAYS)
  }
};

/* Subdivisions and villages the staff meet most, offered before anything
   they have typed themselves. Not an official list - no such list exists
   - so it is a starting point, and the box still takes anything typed. */
window.PH_SUBDIVISIONS = [
  'Alsons Village', 'Amanda Homes', 'Apo Golf and Country Club',
  'Bangkal Village', 'Camella Davao', 'Camella Homes Toril',
  'Catalunan Homes', 'Cedarwood Residences', 'Centro Verde',
  'Com Villa Subdivision', 'Crown Asia', 'Dacoville Subdivision',
  'Davao Diamond Village', 'Deca Homes Cabantian', 'Deca Homes Indangan',
  'Deca Homes Mintal', 'Deca Homes Tacunan', 'Doña Luisa Subdivision',
  'Doña Pilar Village', 'Dumoy Proper', 'Ecoland Subdivision',
  'Emily Homes', 'GSIS Heights Matina', 'Granville Subdivision',
  'Green Meadows', 'Hillcrest Village', 'Ilumina Estates',
  'Insular Village', 'Juna Subdivision', 'Ladislawa Village',
  'Lanang Suites', 'Las Terrazas', 'Maa Residences', 'Mandug Village',
  'Maria Luisa Subdivision', 'Matina Enclaves', 'Metroview Subdivision',
  'Monteritz Classic Estates', 'NHA Bangkal', 'Northtown Davao',
  'Oakridge Village', 'Orchard Village', 'Palm Village',
  'Phoenix Homes', 'Pink Village', 'Rosewood Subdivision',
  'Royal Pines', 'San Pedro Village', 'Sandawa Homes',
  'Sta. Lucia Homes', 'Sterling Heights', 'The Hillside Residences',
  'Tierra Monte', 'Tulip Drive Village', 'Ulas Village',
  'Villa Angelica', 'Villa Esperanza', 'Woodridge Park'
];

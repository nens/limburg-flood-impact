# Water in Balans pandentool
De Water in Balans pandentool bepaalt op basis van een set van maximale waterdieptekaarten (rasters) en panden (polygonen) het risico op wateroverlast en de herkomst van het overlast gevende water. 

Er zijn 3 manieren om de tool te gebruiken, die elk hieronder zullen worden toegelicht 
- In QGIS (de makkelijkste manier om de tool eenmalig te runnen)
- Via de command line (vooral handig voor de verwerking van meerdere scenarios op een reproduceerbare manier)
- In een Python script (voor de verwerking van meerdere scenarios op een reproduceerbare manier en voor de integratie van deze analyse in grotere Python workflows)

## Gebruikershandleiding: QGIS plugin
### Installatie
_Afhankelijk van de distributiewijze_

Na de installatie zal er in de Processing Toolbox in de categorie 'Limburg Flood Impact' een aantal processing algorithms zijn toegevoegd. Deze dienen in een bepaalde volgorde te worden doorlopen. Zie hiervoor het stappenplan.

### Stappenplan
1. Verzamel de benodigde data en voeg deze toe aan het QGIS project. Zie voor meer details hierover de paragraaf 'Invoer en uitvoer'.
2. Voer achter elkaar de processing algorithms uit. Voor de juiste volgorde en meer informatie, zie de paragraaf 'Methode en stappenplan'. Controleer na het uitvoeren van elke stap de attribute table van de pandentabel.
3. Als je niet kan programmeren maar dit proces wel verder wilt automatiseren, dan kan dat binnen QGIS met de Graphical Modeler. Zie hiervoor https://docs.qgis.org/3.22/en/docs/user_manual/processing/modeler.html


## Gebruikershandleiding: Command line
Om de tool via de command line te kunnen gebruiken, heb je Python nodig en moet je de python library `limburg-flood-impact` nodig.

`> pip install limburg-flood-impact`

Vervolgens kan je de verschillende stappen uitvoeren door het betreffende commando als volgt aan te roepen:

`> check_address -b path_to_buildings_data -a path_to_adress_data`

Meer informatie over de specifieke manier om elk script aan te roepen kan met het argument `-h`:

`> check_address -h`

Voor een uitgebreidere uitleg over de argumenten van deze scripts, zie onder "Invoer en uitvoer"

## Gebruikershandleiding: Python
Installeer het python package limburg-flood-impact

`> pip install limburg-flood-impact`

Voer de stappen uit zoals beschreven in de paragraaf "Methode en stappenplan". Let erop dat alle data voldoet aan de eisen die daaraan worden gesteld in "Invoer en uitvoer".

## Invoer en uitvoer
### Panden ('buildings')
_Beschrijving_: Deze input moet een selectie zijn uit de BAG. De makkelijkste manier om deze data (in het juiste formaat) te verkrijgen is door een selectie te maken uit de PDOK WFS service `BAG WFS: pand` en deze selectie op te slaan in een GeoPackage. In QGIS is deze WFS service beschikbaar via de PDOK Services plugin.
_Geometrietype_: Polygon
_Verplicht attribuut_: identificatie (string)
_Bestandsformaat_: GeoPackage

### Verblijfsobjecten ('addresses')
_Beschrijving_: Deze input moet een selectie zijn uit de BAG. De makkelijkste manier om deze data (in het juiste formaat) te verkrijgen is door een selectie te maken uit de PDOK WFS service `BAG WFS: Verblijfsobject` en deze selectie op te slaan in een GeoPackage. In QGIS is deze WFS service beschikbaar via de PDOK Services plugin.
_Geometrietype_: Point
_Verplicht attribuut_: pandidentificatie (string)
_Bestandsformaat_: GeoPackage

### Maximale waterdiepte ('T10', 'T25', 'T100')
_Beschrijving_: Een raster waarvan elke pixels de maximale waterdiepte (in m boven maaiveld) beschrijft die optreedt bij een bui met een herhalingstijd van resp. 10, 25 of 100 jaar.  
_Bestandsformaat_: GeoTIFF (.tif of .tiff)
_Datatype_: Float32
_Overige eisen_: 
- resolutie moet onderling hetzelfde zijn
- eenheid is waterdiepte in m boven maaiveld (dus geen waterstand in m NAP!)
- Nodatavalue is gedefinieerd
- Projectie is Rijksdriehoekstelsel (Nieuw) (EPSG:28992)

## Methode en stappenplan
De methode bestaat uit vier stappen. In elke stap wordt er meer informatie over elk pand bekend; de methode wordt zo ingericht, dat al deze informatie beschikbaar blijft en als attributen aan het pand worden toegevoegd. 

### 1.	Bepalen of panden een adres hebben
#### Gebruik
_QGIS_: Check Addresses

_Command line_: `check_addresses -h`

_Python_:
```
from limburg_flood_impact.check_address import check_building_have_address
from pathlib import Path

buildings_path = Path("C:/Temp/buildings.gpkg")
addresses_path = Path("C:/Temp/adresses.gpkg")
check_building_have_address(buildings_path, adresses_path)
```

#### Algoritme
Aan de panden wordt het veld `heeft_adres` (boolean) toegevoegd. Dit attribuut krijgt de waarde True als het pand gekoppeld kan worden aan een verblijfsobject op basis van `pand.identificatie = verblijfsobject.pandidentificatie` en anders de waarde False.

### 2.	Kwetsbare panden classificeren per neerslagverdeling (stedelijke/landelijke/gebiedsbrede neerslag)
#### Gebruik
_QGIS_: 
- Classify Area Wide Rain
- Classify Rural Rain
- Classify Urban Rain

_Command line_: 
- `classify_area_wide_rain -h`  
- `classify_urban_rain -h`  
- `classify_rural_rain -h`  

_Python_:
```
from limburg_flood_impact.classify_area_wide_rain import classify_area_wide_rain, classify_rural_rain, classify_urban_rain
from pathlib import Path

buildings_path = Path("C:/Temp/buildings.gpkg")
t10_path = Path("C:/Temp/water_depth_t10.tif")
t25_path = Path("C:/Temp/water_depth_t25.tif")
t100_path = Path("C:/Temp/water_depth_t100.tif")

classify_urban_rain(buildings_path, t10_path, t25_path, t100_path)
classify_rural_rain(buildings_path, t10_path, t25_path, t100_path)
classify_area_wide_rain(buildings_path, t10_path, t25_path, t100_path)
```
#### Algoritme
_NB: de hieronder beschreven 'bewerkingen' van de waterdieptekaart gelden alleen voor de bepaling van het risico op wateroverlast per pand. Voor andere doeleinden (zoals kaarten) blijft de oorspronkelijke waterdieptekaart behouden._

De maximale waterdiepte wordt steeds bepaald door het pand te bufferen met 1x de pixelgrootte en van alle pixels die binnen die buffer liggen de maximale waarde te nemen.

Neerslag op stedelijk gebied: 
- Waterdieptepixels met waterdiepte < 2 cm worden verwijderd (op nodata gezet)
- Dit raster wordt gepolygoniseerd
- Waterdieptepixels die in polygonen liggen die kleiner zijn dan 200 m2 worden verwijderd (op nodata gezet)
- De maximale waterdiepte tegen de gevel wordt bepaald
- Is de maximale waterdiepte groter dan 15 cm, dan krijgt dit pand de tussenclassificatie "Risico" (in het attribuut stedelijk_t10 / stedelijk_t25 / stedelijk_t100)
- Is de maximale waterdiepte kleiner of gelijk aan 15 cm, dan krijgt dit pand de tussenclassificatie "Geen risico"

Neerslag op landelijk gebied: 
- Waterdieptepixels met waterdiepte < 2 cm worden verwijderd (op nodata gezet)
- Dit raster wordt gepolygoniseerd
- Waterdieptepixels die in polygonen liggen die kleiner zijn dan 200 m2 worden verwijderd (op nodata gezet)
- De maximale waterdiepte tegen de gevel wordt bepaald
- Is de maximale waterdiepte groter dan 15 cm, dan krijgt dit pand de tussenclassificatie "Kwetsbaar pand door landelijke neerslag"
- Is de maximale waterdiepte kleiner of gelijk aan 15 cm, dan krijgt dit pand de tussenclassificatie "geen kwetsbaar pand door landelijke neerslag"

Neerslag gebiedsbreed:
- Waterdieptepixels met waterdiepte < 2 cm worden verwijderd (op nodata gezet)
- De maximale waterdiepte tegen de gevel wordt bepaald. Dit is de "maximale waterdiepte inclusief kleine plassen"
- Het waterdiepteraster zonder pixels < 2 cm wordt gepolygoniseerd
- Waterdieptepixels die in polygonen liggen die kleiner zijn dan 200 m2 worden verwijderd (op nodata gezet)
- De maximale waterdiepte tegen de gevel wordt opnieuw bepaald. Dit is de "maximale waterdiepte exclusief kleine plassen"
- Is de maximale waterdiepte inclusief kleine plassen ≤ 15 cm, dan krijgt dit pand de tussenclassificatie "geen kwetsbaar pand door gebiedsbrede neerslag"
- Is de maximale waterdiepte exclusief kleine plassen > 15 cm, dan krijgt dit pand de tussenclassificatie "Kwetsbaar pand door gebiedsbrede neerslag, regionale herkomst".
- Is de maximale waterdiepte inclusief kleine plassen > 15 cm, maar de maximale waterdiepte exclusief kleine plassen ≤ 15 cm, dan krijgt dit pand de tussenclassificatie "risicopand door gebiedsbrede neerslag, lokale herkomst".

### 3. Samengevoegde classificatie per bui (T10/T25/T100)
#### Gebruik

_QGIS_: Combine Classification

_Command line_: `combine_classification -h`

_Python_:
```
from limburg_flood_impact.combine_classification import combine_classification
from pathlib import Path

buildings_path = Path("C:/Temp/buildings.gpkg")

combine_classification(buildings_path)
```

#### Algoritme
In deze stap worden de tussenclassificaties per neerslaggebied vertaald naar 1 klasse per pand per bui. Dit wordt gedaan met de vertaaltabel https://github.com/nens/limburg-flood-impact/blob/main/misc/classificatie.xlsx

### 4. Toetsing aan de norm
#### Gebruik
**DIT AANPASSEN ALS DIT ONDERDEEL GEIMPLEMENTEERD IS**

_QGIS_: **Naam van het processing algorithm in QGIS**

_Command line_: `classify_area_wide_rain -h`

_Python_:
```
python_code_snippet
```

#### Algoritme
Optioneel kan elk pand getoetst worden aan de norm. Daarbij wordt de volgende methodiek gehanteerd:
- Bepalen in welk normgebied het pand ligt. Eerst wordt in de boolean velden in_normgebied_t10, in_normgebied_t25 en in_normgebied_t100 genoteerd of het pand (deels) in het betreffende normgebied ligt. 
- Vervolgens wordt in het string veld ‘normgebied’ genoteerd welke norm van toepassing is. Ligt het pand in meer dan 1 normgebied (pand ligt op de grens), dan wordt de hoogste norm aangehouden (T100 boven T25 boven T10 boven Geen norm).
- Als het pand de norm "T100" heeft toegekend gekregen, wordt de klasse voor de T100 bui overgenomen in het attribuut “toetsingsklasse”
- Als het pand de norm "T25" heeft toegekend gekregen, wordt de klasse voor de T25 bui overgenomen in het attribuut “toetsingsklasse”
- Als het pand de norm "T10" heeft toegekend gekregen, wordt de klasse voor de T10 bui overgenomen in het attribuut “toetsingsklasse”
- Als het pand de norm "Geen norm" heeft toegekend gekregen, wordt “n.v.t.” ingevuld in het attribuut “toetsingsklasse”
- De toetsingsklasse wordt vervolgens vertaald naar "Voldoet aan norm" (ja/nader onderzoeken). Zie de vertaaltabel in de bijlage.
- Nader onderzoek moet voor de betreffende panden uitwijzen:
  - Is het wateroverlastrisico reëel of een artefact de GIS analyse of van het hydrodynamisch rekenmodel?
  - Is de totale afstroming uit landelijk gebied hoger dan de drempelwaarde (750 m3 bij 33 mm in 20 minuten, of 1250 m3 bij T25)?
- In de tool geven we de gebruiker de mogelijkheid een polygoon op te geven van het gebied waar de afstroming boven deze drempelwaarde uitkomt. Als het pand geheel binnen deze polygoon ligt en het attribuut “Voldoet aan norm” de waarde “nader onderzoeken” heeft, wordt “voldoet aan norm” geüpdate naar “nee”.


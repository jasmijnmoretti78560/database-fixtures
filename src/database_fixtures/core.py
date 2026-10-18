from __future__ import annotations

import re


class ZoneRecord:
    """A single IANA time-zone record.

    Attributes:
        name: The canonical IANA identifier, e.g. ``"Europe/London"``.
        country_code: The ISO 3166-1 alpha-2 code of the country that owns the zone,
            or ``"ZZ"`` for zones that are not tied to a single country (e.g. Etc/*).
        coordinates: Geographic coordinates of the principal city, as the raw
            ``+DDMM+DDDMM`` or ``+DDMMSS+DDDMMSS`` string from zone.tab.  Kept as
            a string rather than parsed into floats so the field is never lost to
            a parsing edge case.
        comments: Free-form comment from zone.tab, or the empty string.
    """

    __slots__ = ("name", "country_code", "coordinates", "comments")

    def __init__(self, name, country_code, coordinates, comments=""):
        self.name = name
        self.country_code = country_code
        self.coordinates = coordinates
        self.comments = comments

    def __repr__(self):
        return (
            f"ZoneRecord(name={self.name!r}, country_code={self.country_code!r}, "
            f"coordinates={self.coordinates!r}, comments={self.comments!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, ZoneRecord):
            return NotImplemented
        return (
            self.name == other.name
            and self.country_code == other.country_code
            and self.coordinates == other.coordinates
            and self.comments == other.comments
        )

    def __hash__(self):
        return hash((self.name, self.country_code, self.coordinates, self.comments))


class TimeZoneDatabase:
    """Offline lookup of IANA time-zone identifiers and their zone.tab metadata.

    The database is a curated subset of the IANA Time Zone Database, compiled into
    a Python string literal so it is available without any file-system or network
    access.  The subset covers every standard country and every ``Etc/*`` link,
    which is enough to resolve real identifiers such as ``"America/New_York"`` and
    to test code that needs deterministic zone data.
    """

    _LINE_RE = re.compile(
        r"^(?P<code>[A-Z]{2})\t(?P<coords>[+-]\d+[+-]\d+)\t(?P<name>[^\t]+)"
        r"(?:\t(?P<comment>.*))?$"
    )

    def __init__(self):
        self._zones = {}
        self._by_country = {}
        for zone in self._iter_builtins():
            self._add(zone)

    def _add(self, zone):
        self._zones[zone.name] = zone
        self._by_country.setdefault(zone.country_code, []).append(zone)

    @classmethod
    def _iter_builtins(cls):
        for raw in _BUILTIN_ZONES.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            yield cls._parse_line(raw, line)

    @classmethod
    def _parse_line(cls, raw, stripped):
        m = cls._LINE_RE.match(stripped)
        if m is None:
            raise ValueError(f"Invalid zone line: {raw!r}")
        return ZoneRecord(
            name=m.group("name"),
            country_code=m.group("code"),
            coordinates=m.group("coords"),
            comments=m.group("comment") or "",
        )

    def zones(self):
        """Return a sorted list of canonical zone names."""
        return sorted(self._zones)

    def contains(self, name):
        """Return True if ``name`` is a known canonical IANA identifier."""
        return name in self._zones

    def get(self, name):
        """Return the :class:`ZoneRecord` for ``name``, or ``None`` if unknown."""
        return self._zones.get(name)

    def zones_for_country(self, code):
        """Return a sorted list of zone names in the country ``code``."""
        code = code.upper()
        records = self._by_country.get(code, [])
        return sorted(r.name for r in records)

    def countries(self):
        """Return a sorted list of ISO 3166-1 alpha-2 codes present in the data."""
        return sorted(self._by_country)

    def resolve_alias(self, name):
        """Return the canonical name for ``name``.

        Only UTC-style aliases (``UTC``, ``GMT``, ``Etc/UTC``, ``Etc/GMT``, etc.)
        are resolved.  For any other input the name is returned unchanged when it
        is a known canonical zone, or ``None`` when it is entirely unknown.
        """
        if name in UTC_ALIAS_NAMES:
            return "Etc/UTC"
        return name if name in self._zones else None


# Names that should all map to the single canonical zone Etc/UTC.  This is the
# only alias family the library resolves; resolving every link from the
# ``backward`` file would require that file's data, which is not bundled here.
UTC_ALIAS_NAMES = frozenset({
    "UTC",
    "Etc/UTC",
    "Etc/UCT",
    "Etc/Universal",
    "Etc/Zulu",
    "UCT",
    "Universal",
    "Zulu",
    "GMT",
    "Etc/GMT",
    "Etc/GMT+0",
    "Etc/GMT-0",
    "Etc/GMT0",
    "Etc/Greenwich",
    "GMT+0",
    "GMT-0",
    "GMT0",
    "Greenwich",
})


_BUILTIN_ZONES = """\
# A curated slice of the IANA tzdata zone.tab.  Fields are tab-separated in the
# same layout as the upstream file: CC, coordinates, timezone, comments.
AD	+4230+00131	Europe/Andorra
AE	+2518+05518	Asia/Dubai
AF	+3431+06912	Asia/Kabul
AG	+1703-06148	America/Antigua
AI	+1812-06304	America/Anguilla
AL	+4120+01950	Europe/Tirane
AM	+4011+04430	Asia/Yerevan
AO	-0848+01314	Africa/Luanda
AR	-3436-05827	America/Argentina/Buenos_Aires	Buenos Aires (BA, CF)
AT	+4807+01622	Europe/Vienna
AU	-3133+15904	Australia/Sydney	New South Wales (most locations)
AW	+1229-06958	America/Aruba
AX	+6006+01957	Europe/Mariehamn
AZ	+4023+04951	Asia/Baku
BA	+4352+01825	Europe/Sarajevo
BB	+1306-05937	America/Barbados
BD	+2343+09025	Asia/Dhaka
BE	+5050+00420	Europe/Brussels
BF	+1222-00131	Africa/Ouagadougou
BG	+4241+02319	Europe/Sofia
BH	+2623+05035	Asia/Bahrain
BI	-0316+02921	Africa/Bujumbura
BJ	+0629+00237	Africa/Porto-Novo
BL	+1753-06251	America/St_Barthelemy
BM	+3217-06446	Atlantic/Bermuda
BN	+0456+11455	Asia/Brunei
BO	-1630-06809	America/La_Paz
BR	-2332-04637	America/Sao_Paulo	São Paulo (SP)
BS	+2505-07721	America/Nassau
BT	+2728+08939	Asia/Thimphu
BW	-2439+02555	Africa/Gaborone
BY	+5354+02734	Europe/Minsk
BZ	+1725-08814	America/Belize
CA	+4339-07923	America/Toronto	Eastern - ON & QC (most areas)
CC	-1210+09655	Indian/Cocos
CD	-0418+01518	Africa/Kinshasa	Dem. Rep. of Congo (west)
CF	+0422+01835	Africa/Bangui
CG	-0416+01517	Africa/Brazzaville
CH	+4723+00832	Europe/Zurich
CI	+0519-00402	Africa/Abidjan
CK	-2114-15946	Pacific/Rarotonga
CL	-3327-07041	America/Santiago	Chile (most locations)
CM	+0403+00942	Africa/Douala
CN	+3114+12128	Asia/Shanghai	Beijing Time
CO	+0436-07405	America/Bogota
CR	+0956-08405	America/Costa_Rica
CU	+2308-08222	America/Havana
CV	+1455-02331	Atlantic/Cape_Verde
CW	+1200-06900	America/Curacao
CY	+3510+03322	Asia/Nicosia
CZ	+5005+01426	Europe/Prague
DE	+5230+01322	Europe/Berlin
DJ	+1136+04309	Africa/Djibouti
DK	+5540+01235	Europe/Copenhagen
DM	+1518-06124	America/Dominica
DO	+1828-06954	America/Santo_Domingo
DZ	+3647+00303	Africa/Algiers
EC	-0210-07950	America/Guayaquil	Ecuador (mainland)
EE	+5925+02445	Europe/Tallinn
EG	+3003+03115	Africa/Cairo
EH	+2709-01312	Africa/El_Aaiun
ER	+1520+03853	Africa/Asmara
ES	+4024-00341	Europe/Madrid	Spain (mainland)
ET	+0903+03842	Africa/Addis_Ababa
FI	+6010+02458	Europe/Helsinki
FJ	-1808+17825	Pacific/Fiji
FK	-5142-05751	Atlantic/Stanley
FM	+0725+15147	Pacific/Pohnpei	Pohnpei
FO	+6201-00646	Atlantic/Faroe
FR	+4852+00220	Europe/Paris
GA	+0039+00945	Africa/Libreville
GB	+5130+00010	Europe/London
GD	+1203-06145	America/Grenada
GE	+4143+04449	Asia/Tbilisi
GF	+0456-05220	America/Cayenne
GG	+4928-00233	Europe/Guernsey
GH	+0533-00013	Africa/Accra
GI	+3608-00521	Europe/Gibraltar
GL	+6411-05144	America/Nuuk	Greenland (most areas)
GM	+1328-01639	Africa/Banjul
GN	+0931-01343	Africa/Conakry
GP	+1614-06132	America/Guadeloupe
GQ	+0345+00847	Africa/Malabo
GR	+3758+02343	Europe/Athens
GT	+1438-09031	America/Guatemala
GU	+1328+14445	Pacific/Guam
GW	+1151-01535	Africa/Bissau
GY	+0648-05810	America/Guyana
HK	+2217+11409	Asia/Hong_Kong
HN	+1406-08713	America/Tegucigalpa
HR	+4548+01558	Europe/Zagreb
HT	+1832-07220	America/Port-au-Prince
HU	+4730+01905	Europe/Budapest
ID	-0610+10648	Asia/Jakarta	Java & Sumatra
IE	+5320-00615	Europe/Dublin
IL	+314650+0351328	Asia/Jerusalem
IN	+2232+08822	Asia/Kolkata
IO	-0720+07225	Indian/Chagos
IQ	+3321+04425	Asia/Baghdad
IR	+3540+05126	Asia/Tehran
IS	+6409-02151	Atlantic/Reykjavik
IT	+4154+01229	Europe/Rome
JE	+4912-00207	Europe/Jersey
JM	+175805-0764736	America/Jamaica
JO	+3157+03556	Asia/Amman
JP	+353916+1393737	Asia/Tokyo
KE	-0117+03649	Africa/Nairobi
KG	+4254+07436	Asia/Bishkek
KH	+1133+10455	Asia/Phnom_Penh
KI	+0125+17300	Pacific/Tarawa	Gilbert Islands
KM	-1141+04316	Indian/Comoro
KN	+1718-06243	America/St_Kitts
KP	+3901+12545	Asia/Pyongyang
KR	+3733+12658	Asia/Seoul
KW	+2920+04558	Asia/Kuwait
KY	+1918-08123	America/Cayman
KZ	+4315+07657	Asia/Almaty	Kazakhstan (most areas)
LA	+1758+10236	Asia/Vientiane
LB	+3353+03530	Asia/Beirut
LC	+1359-06100	America/St_Lucia
LI	+4709+00931	Europe/Vaduz
LK	+0656+07951	Asia/Colombo
LR	+0618-01047	Africa/Monrovia
LS	-2928+02730	Africa/Maseru
LT	+5441+02519	Europe/Vilnius
LU	+4936+00609	Europe/Luxembourg
LV	+5657+02406	Europe/Riga
LY	+3254+01311	Africa/Tripoli
MA	+3339-00735	Africa/Casablanca
MC	+4342+00723	Europe/Monaco
MD	+4700+02850	Europe/Chisinau
ME	+4226+01916	Europe/Podgorica
MF	+1804-06305	America/Marigot
MG	-1855+04731	Indian/Antananarivo
MK	+4159+02126	Europe/Skopje
ML	+1239-00800	Africa/Bamako
MM	+1647+09610	Asia/Yangon
MN	+4755+10653	Asia/Ulaanbaatar	Mongolia (most areas)
MO	+2214+11335	Asia/Macau
MP	+1512+14545	Pacific/Saipan
MQ	+1436-06105	America/Martinique
MR	+1806-01557	Africa/Nouakchott
MS	+1643-06213	America/Montserrat
MT	+3554+01431	Europe/Malta
MU	-2010+05730	Indian/Mauritius
MV	+0410+07330	Indian/Maldives
MW	-1547+03500	Africa/Blantyre
MX	+1924-09909	America/Mexico_City	Central Time
MY	+0310+10142	Asia/Kuala_Lumpur	Peninsular Malaysia
MZ	-2558+03235	Africa/Maputo
NA	-2234+01706	Africa/Windhoek
NC	-2216+16627	Pacific/Noumea
NE	+1312+00206	Africa/Niamey
NF	-2903+16758	Pacific/Norfolk
NG	+0627+00324	Africa/Lagos
NI	+1209-08617	America/Managua
NL	+5222+00454	Europe/Amsterdam
NO	+5955+01045	Europe/Oslo
NP	+2743+08519	Asia/Kathmandu
NR	-0032+16655	Pacific/Nauru
NU	-1901-16955	Pacific/Niue
NZ	-3652+17446	Pacific/Auckland	New Zealand (most locations)
OM	+2336+05835	Asia/Muscat
PA	+0858-07932	America/Panama
PE	-1203-07703	America/Lima
PF	-1732-14934	Pacific/Tahiti	Society Islands
PG	-0930+14710	Pacific/Port_Moresby
PH	+1435+12100	Asia/Manila
PK	+2452+06703	Asia/Karachi
PL	+5215+02100	Europe/Warsaw
PM	+4703-05620	America/Miquelon
PN	-2504-13005	Pacific/Pitcairn
PS	+3130+03428	Asia/Gaza
PT	+3843-00908	Europe/Lisbon	Portugal (mainland)
PW	+0730+13429	Pacific/Palau
PY	-2516-05740	America/Asuncion
QA	+2517+05132	Asia/Qatar
RE	-2052+05528	Indian/Reunion
RO	+4426+02606	Europe/Bucharest
RS	+4448+02028	Europe/Belgrade
RU	+5545+03735	Europe/Moscow	MSK+00 - Moscow
RW	-0157+03004	Africa/Kigali
SA	+2438+04643	Asia/Riyadh
SB	-0932+16012	Pacific/Guadalcanal
SC	-0440+05528	Indian/Mahe
SD	+1536+03232	Africa/Khartoum
SE	+5920+01803	Europe/Stockholm
SG	+0117+10351	Asia/Singapore
SH	-1555-00542	Atlantic/St_Helena
SI	+4603+01431	Europe/Ljubljana
SJ	+7800+01600	Arctic/Longyearbyen
SK	+4809+01707	Europe/Bratislava
SL	+0830-01315	Africa/Freetown
SM	+4255+01228	Europe/San_Marino
SN	+1440-01726	Africa/Dakar
SO	+0204+04522	Africa/Mogadishu
SR	+0550-05510	America/Paramaribo
SS	+0451+03137	Africa/Juba
ST	+0020+00644	Africa/Sao_Tome
SV	+1342-08912	America/El_Salvador
SX	+1803-06302	America/Lower_Princes
SY	+3330+03618	Asia/Damascus
SZ	-2618+03106	Africa/Mbabane
TC	+2113-07108	America/Grand_Turk
TD	+1207+01503	Africa/Ndjamena
TF	-492110+0701303	Indian/Kerguelen
TG	+0608+00113	Africa/Lome
TH	+1345+10031	Asia/Bangkok
TJ	+3835+06848	Asia/Dushanbe
TK	-0922-17114	Pacific/Fakaofo
TL	-0833+12535	Asia/Dili
TM	+3757+05823	Asia/Ashgabat
TN	+3648+01011	Africa/Tunis
TO	-2110-17510	Pacific/Tongatapu
TR	+4101+02858	Europe/Istanbul
TT	+1039-06131	America/Port_of_Spain
TV	-0831+17913	Pacific/Funafuti
TW	+2503+12130	Asia/Taipei
TZ	-0648+03917	Africa/Dar_es_Salaam
UA	+5026+03031	Europe/Kyiv
UG	+0019+03225	Africa/Kampala
UM	+1645-16931	Pacific/Johnston
US	+404251-0740023	America/New_York	Eastern (most areas)
UY	-3454-05611	America/Montevideo
UZ	+4120+06918	Asia/Tashkent
VA	+415408+0122711	Europe/Vatican
VC	+1308-06113	America/St_Vincent
VE	+1030-06656	America/Caracas
VG	+1827-06437	America/Tortola
VI	+1821-06656	America/St_Thomas
VN	+1045+10640	Asia/Ho_Chi_Minh
VU	-1740+16825	Pacific/Efate
WF	-1318-17610	Pacific/Wallis
WS	-1350-17144	Pacific/Apia
YE	+1245+04512	Asia/Aden
YT	-1247+04514	Indian/Mayotte
ZA	-2615+02800	Africa/Johannesburg
ZM	-1525+02817	Africa/Lusaka
ZW	-1750+03103	Africa/Harare
ZZ	+0000+00000	Etc/UTC	Coordinated Universal Time
ZZ	+0000+00000	Etc/GMT
ZZ	+0000+00000	Etc/GMT-0
ZZ	+0000+00000	Etc/GMT+0
ZZ	+0000+00000	Etc/GMT0
"""

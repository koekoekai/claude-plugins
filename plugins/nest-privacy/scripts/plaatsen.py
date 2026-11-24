"""Plaatsen en landen: met hoofdletter midden in een zin, maar geen persoon. Kleine letters, zonder accenten waar dat gangbaar is.
Samengesteld uit Nederlandse gemeenten en grote kernen, Vlaamse steden en grote steden en landen elders (algemene kennis)."""

NL = """
aa en hunze aalsmeer aalten achtkarspelen alblasserdam albrandswaard alkmaar almelo almere alphen aan den rijn alphen-chaam
altena ameland amersfoort amstelveen amsterdam apeldoorn arnhem assen asten baarle-nassau baarn barendrecht barneveld beek
beekdaelen beesel berg en dal bergeijk bergen bergen op zoom berkelland bernheze best beuningen beverwijk bladel blaricum
bloemendaal bodegraven-reeuwijk boekel borger-odoorn borne borsele boxtel breda bronckhorst brummen brunssum bunnik bunschoten
buren capelle aan den ijssel castricum coevorden cranendonck culemborg dalfsen dantumadiel de bilt de fryske marren de ronde venen
de wolden delft den helder deurne deventer diemen dijk en waard dinkelland doesburg doetinchem dongen dordrecht drechterland
drimmelen dronten druten duiven echt-susteren edam-volendam ede eemnes eemsdelta eersel eijsden-margraten eindhoven elburg emmen
enkhuizen enschede epe ermelo etten-leur geertruidenberg geldrop-mierlo gemert-bakel gennep gilze en rijen goeree-overflakkee
goes goirle gooise meren gorinchem gouda groningen gulpen-wittem haaksbergen haarlem haarlemmermeer halderberge hardenberg harderwijk
hardinxveld-giessendam harlingen hattem heemskerk heemstede heerde heerenveen heerlen heeze-leende heiloo hellendoorn helmond
hendrik-ido-ambacht hengelo heumen heusden hillegom hilvarenbeek hilversum hoeksche waard hof van twente hollands kroon hoogeveen
hoorn horst aan de maas houten huizen hulst ijsselstein kaag en braassem kampen kapelle katwijk kerkrade koggenland krimpen aan
den ijssel krimpenerwaard laarbeek land van cuijk landgraaf landsmeer lansingerland laren leeuwarden leiden leiderdorp
leidschendam-voorburg lelystad leudal leusden lingewaard lisse lochem loon op zand lopik losser maasdriel maasgouw maashorst
maassluis maastricht medemblik meerssen meierijstad meppel middelburg midden-delfland midden-drenthe midden-groningen moerdijk
molenlanden montferland montfoort mook en middelaar neder-betuwe nederweert nieuwegein nieuwkoop nijkerk nijmegen nissewaard
noardeast-fryslan noord-beveland noordenveld noordoostpolder noordwijk nuenen nunspeet oegstgeest oirschot oisterwijk oldambt
oldebroek oldenzaal olst-wijhe ommen oost gelre oosterhout ooststellingwerf oostzaan opmeer opsterland oss oude ijsselstreek
ouder-amstel oudewater overbetuwe papendrecht peel en maas pekela pijnacker-nootdorp purmerend putten raalte reimerswaal
renkum renswoude reusel-de mierden rheden rhenen ridderkerk rijssen-holten rijswijk roerdalen roermond roosendaal rotterdam
rozendaal rucphen schagen scherpenzeel schiedam schiermonnikoog schouwen-duiveland 's-hertogenbosch den bosch simpelveld
sint-michielsgestel sittard-geleen sliedrecht sluis smallingerland soest someren son en breugel stadskanaal staphorst
stede broec steenbergen steenwijkerland stein stichtse vecht sudwest-fryslan terneuzen terschelling texel teylingen tholen
tiel tilburg tubbergen twenterand tynaarlo tytsjerksteradiel uitgeest uithoorn urk utrecht utrechtse heuvelrug vaals valkenburg
valkenswaard veendam veenendaal veere veldhoven velsen venlo venray vijfheerenlanden vlaardingen vlieland vlissingen voerendaal
voorne aan zee voorschoten voorst vught waadhoeke waalre waalwijk waddinxveen wageningen wassenaar waterland weert west betuwe
west maas en waal westerkwartier westerveld westervoort westerwolde westland weststellingwerf wierden wijchen wijdemeren
wijk bij duurstede winterswijk woensdrecht woerden wormerland woudenberg zaanstad zaltbommel zandvoort zeewolde zeist zevenaar
zoetermeer zoeterwoude zuidplas zundert zutphen zwartewaterland zwijndrecht zwolle den haag 's-gravenhage scheveningen
loosdrecht bussum naarden weesp volendam marken giethoorn kinderdijk breukelen vinkeveen mijdrecht abcoude driebergen
doorn zandvoort ijmuiden hoofddorp nieuw-vennep badhoevedorp schiphol lelystad emmeloord dokkum sneek drachten heerenveen
joure franeker bolsward workum hindeloopen stavoren lemmer winschoten delfzijl appingedam veendam hoogezand
""".split()

BE = """
antwerpen gent brugge brussel bruxelles leuven mechelen aalst kortrijk hasselt genk oostende sint-niklaas roeselare turnhout
lier herentals mol geel tienen diest vilvoorde halle dendermonde lokeren ninove ieper knokke-heist blankenberge waregem
liège luik namur namen charleroi mons bergen wavre waver
""".split()

WERELD = """
nederland belgie belgië duitsland frankrijk engeland schotland ierland spanje portugal italie italië zwitserland oostenrijk
denemarken noorwegen zweden finland polen tsjechie roemenie griekenland turkije marokko suriname indonesie china japan india
amerika canada mexico brazilie australie europa azie afrika
netherlands belgium germany france england scotland ireland spain portugal italy switzerland austria denmark norway sweden
finland poland greece turkey morocco india china japan america canada mexico brazil australia europe asia africa
london manchester birmingham liverpool leeds glasgow edinburgh dublin cork belfast paris lyon marseille lille nice bordeaux
berlin hamburg munich münchen frankfurt cologne köln düsseldorf dusseldorf stuttgart dortmund essen bremen hannover aachen
madrid barcelona valencia sevilla lisbon lisboa porto rome roma milan milano turin napoli venice vienna wien zurich zürich
geneva genève bern basel copenhagen kopenhagen oslo stockholm helsinki warsaw warschau krakow prague praag budapest athens
athene istanbul ankara dubai tokyo beijing shanghai singapore hong kong mumbai delhi bangalore sydney melbourne toronto
vancouver montreal chicago boston seattle austin denver miami atlanta dallas houston phoenix philadelphia washington
san francisco los angeles new york brooklyn manhattan paramaribo jakarta casablanca rabat
""".split()

PLAATSEN = set(NL) | set(BE) | set(WERELD)

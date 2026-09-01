"""
PIN Code lookup API — provides District, State, and Area auto-fill by 6-digit PIN code.
Contains built-in offline dataset from All India PIN Code List + online fallback.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import urllib.request
import json
import logging

logger = logging.getLogger("pincode-service")
router = APIRouter(prefix="/pincode", tags=["PIN Code Lookup"])

class PincodeResponse(BaseModel):
    pincode: str
    district: str
    state: str
    areas: List[str]

# Fast in-memory cache
_PIN_CACHE = {}

# Offline comprehensive dictionary for common regions / major districts from All India Pin Code List
_BUILTIN_PIN_DATA = {
    # Delhi
    "110001": {"district": "New Delhi", "state": "Delhi", "areas": ["Connaught Place", "Baroda House", "Janpath", "Parliament House", "Supreme Court"]},
    "110002": {"district": "Central Delhi", "state": "Delhi", "areas": ["A.G.C.R", "Ajmeri Gate Extension", "Delhi GPO", "Minto Road", "Gandhi Smarak Nidhi"]},
    "110003": {"district": "South Delhi", "state": "Delhi", "areas": ["Aliganj", "Golf Links", "Lodi Road", "Kasturba Nagar"]},
    "110005": {"district": "Central Delhi", "state": "Delhi", "areas": ["Anand Nagar", "Anand Parbat", "Bank Street", "Karol Bagh", "Sat Nagar"]},
    "110006": {"district": "North Delhi", "state": "Delhi", "areas": ["Bara Tooti", "Chandni Chowk", "Chawri Bazar", "Hauz Qazi", "Jama Masjid"]},
    "110007": {"district": "North Delhi", "state": "Delhi", "areas": ["Birla Lines", "Delhi University", "Jawahar Nagar", "R.P.Bagh", "Shakti Nagar"]},
    "110010": {"district": "South West Delhi", "state": "Delhi", "areas": ["505 A.B. Workshop", "A.F.Palam", "C.O.D.", "Pinto Park", "Station Road"]},
    "110011": {"district": "South Delhi", "state": "Delhi", "areas": ["Defence Head Quarters", "Gymkhana Club", "Shahajahan Road", "South Avenue"]},
    "110015": {"district": "West Delhi", "state": "Delhi", "areas": ["Delhi Industrial Area", "Mansarover Garden", "Rattan Park", "Lalit Makan Nagar"]},
    "110016": {"district": "South Delhi", "state": "Delhi", "areas": ["I.I.T", "Technology Bhawan", "Green Park", "Green Park Market"]},
    "110018": {"district": "West Delhi", "state": "Delhi", "areas": ["A.G.I. Vikaspuri", "Ashok Nagar (Tilak Nagar)", "Chand Nagar", "Vikaspuri", "Tilak Nagar"]},
    "110019": {"district": "South Delhi", "state": "Delhi", "areas": ["Alaknanda", "Chitranjan Park", "Govindpuri", "Kalkaji", "Nehru Place"]},
    "110020": {"district": "South Delhi", "state": "Delhi", "areas": ["Flatted Factories Complex", "Okhla Industrial Estate", "Teh Khand"]},
    "110022": {"district": "South West Delhi", "state": "Delhi", "areas": ["R.K.Puram Sector I", "R.K.Puram Sector VII", "R.K.Puram Sector VIII", "R.K.Puram Sector XII"]},
    "110024": {"district": "South Delhi", "state": "Delhi", "areas": ["Amar Colony", "Defence Colony", "Lajpat Nagar"]},
    "110028": {"district": "South West Delhi", "state": "Delhi", "areas": ["Naraina Industrial Estate", "Naraina Industrial Area", "Naraina Village"]},
    "110034": {"district": "North West Delhi", "state": "Delhi", "areas": ["Anandvas", "Maurya Enclave", "S.B. Railway Station", "Shakurpur"]},
    "110052": {"district": "North West Delhi", "state": "Delhi", "areas": ["Ashok Vihar HO", "Nimri", "Shastri Nagar", "Satyavati Nagar"]},
    "110065": {"district": "South Delhi", "state": "Delhi", "areas": ["East of Kailash", "New Friends Colony", "Sant Nagar", "Srinivasapuri"]},
    "110085": {"district": "North West Delhi", "state": "Delhi", "areas": ["Rohini", "Prashant Vihar"]},
    "110092": {"district": "East Delhi", "state": "Delhi", "areas": ["Anand Vihar", "I. P. Extension", "Mandawali Fazalpur", "Shakarpur", "Suraj Mal Vihar", "Yojna Vihar"]},

    # Rajasthan - Jaipur
    "302001": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Jaipur G.P.O", "Ashok Nagar (Jaipur)", "Chand Pol Bazar", "Jodhpur City", "M.I.Road", "Purani Basti", "Rajasthan State Hotel", "Ramganj Bazar", "Station Road"]},
    "302002": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Amer Road", "Jalebi Chowk", "Jaipur Tripolia Bazar", "Moti Katla Bazar", "Shivaji Nagar"]},
    "302003": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Haldiyon Ka Rasta", "Jaipur City", "Johri Bazar", "R.A.C.Jaipur", "Krishi Upaj Mandi"]},
    "302004": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Arjunlal Sethi Nagar", "Jawahar Nagar", "Moti Dungri Road", "Raja Park Colony", "Rajasthan University", "Tilak Nagar"]},
    "302005": {"district": "Jaipur", "state": "Rajasthan", "areas": ["A.G. Office (Jaipur)", "Jaipur Rajasthan Secretariate", "Vidyut Bhawan"]},
    "302006": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Ajmer Road (Jaipur)", "Jaipur R.S", "Khatipura Road", "Station Road"]},
    "302011": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Jaipur A.P.Sanganer", "Sanganer"]},
    "302012": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Amba Bari", "Dahar Ka Balaji", "Jaipur Jhotwara", "Khatipura", "Jhotwara Industrial Area"]},
    "302015": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Bapu Nagar", "Jaipur Bajaj Nagar", "S.D.M.Hospital"]},
    "302016": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Bani Park", "Collectorate", "Jaipur Shastri Nagar", "Sindhi Colony"]},
    "302017": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Amer Clark Hotel", "Malviya Industrial Area", "Malviya Nagar", "Sector 11/12 Malviya Nagar"]},
    "302018": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Durgapura", "Rampura Roopa"]},
    "302020": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Mansarover", "Mansarover SFS"]},
    "302021": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Vaishali Nagar"]},
    "302022": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Sitapura I.A."]},
    "303002": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Achrol"]},
    "303007": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Bagru"]},
    "303901": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Chaksu"]},
    "303702": {"district": "Jaipur", "state": "Rajasthan", "areas": ["Chomu", "Chiomu Triplia Bazar"]},

    # Rajasthan - Jodhpur
    "342001": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur H.O", "Jodhpur Aerodrome", "Jodhpur Cloth Market", "Jodhpur Railway Office", "Jodhpur Ratnada Bazar", "Jodhpur University Campus", "Ratnada"]},
    "342002": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur Girdikot", "Jodhpur Katla Bazar", "Jodhpur Nagorion-Ka-Bass"]},
    "342003": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur Chopasani Road", "Jodhpur Gandhi Maidan", "Jodhpur Jalori Gate", "Jodhpur Massuria", "Jodhpur Shastri Circle"]},
    "342004": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur Pratap Nagar"]},
    "342005": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur Bhagat-Ki-Kothi"]},
    "342006": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur Kacheri", "Jodhpur Mahamandir Bazar", "Jodhpur Mandore Road", "Jodhpur Nagori Gate", "Jodhpur Udai Mandir", "Jodhpur Umed Bhawan"]},
    "342008": {"district": "Jodhpur", "state": "Rajasthan", "areas": ["Jodhpur Nandanwan"]},

    # Rajasthan - Udaipur
    "313001": {"district": "Udaipur", "state": "Rajasthan", "areas": ["Udaipur City", "Udaipur H.O", "Ashok Nagar Udaipur Shastri Circle", "Booharwadi Udaipur", "Chandpole Udaipur", "Pratap Nagar Udaipur", "Railway Station Udaipur", "Tourist Complex Udaipur", "Surajpole Udaipur"]},
    "313002": {"district": "Udaipur", "state": "Rajasthan", "areas": ["Dabok", "Delwara"]},
    "313023": {"district": "Udaipur", "state": "Rajasthan", "areas": ["Dabok Airport"]},

    # Rajasthan - Ajmer
    "305001": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer HO", "Asha Ganj", "Jones Ganj Ajmer", "Naya Bazar Ajmer", "R.P.S.C Ajmer", "Raj Eduction Board Ajmer", "Session Cour Ajmer", "Sunder Vilas Ajmer"]},
    "305002": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer Indl. Estate Makhupura"]},
    "305003": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer Hmt"]},
    "305004": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer Regional College"]},
    "305005": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer CRPF", "Christianganj Ajmer"]},
    "305006": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer Shastri Nagar", "Ashok Mark Ajmer"]},
    "305007": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Ajmer G.C. Road", "Pal Beesla Ajmer"]},
    "305008": {"district": "Ajmer", "state": "Rajasthan", "areas": ["Adarshnagar Ajmer", "Alwar Gate(Ajmer)", "Bhajanganj(Ajmer)", "Gulab Bari Ajmer", "Loco Workshop Ajmer", "Mayo Ajmer", "Police Line Ajmer"]},

    # Rajasthan - Kota
    "324001": {"district": "Kota", "state": "Rajasthan", "areas": ["Kota City", "Kota Cutchery", "Kota Kunadi", "Kota Nayapura", "Subhasmarg"]},
    "324002": {"district": "Kota", "state": "Rajasthan", "areas": ["Kota JN", "Gurudwara Road (Kota)", "New Rly.Colony (Kota)", "Wrc Kota"]},
    "324005": {"district": "Kota", "state": "Rajasthan", "areas": ["Kota Pip", "Mahaveernagar", "Pip Indra Prastha", "Pip Vigyan Nagar", "Talwandi(Kota Pip)"]},
    "324006": {"district": "Kota", "state": "Rajasthan", "areas": ["Ghantaghar Kota", "Khaithoonipole Kota", "Surajpole Kota"]},
    "324007": {"district": "Kota", "state": "Rajasthan", "areas": ["CR Pura (Kota)", "Kota New Grainmandi", "Gumanpura Kota", "Kotrigrdhanpura", "Small Industraial Area", "Vallabah Nagar"]},

    # Maharashtra - Mumbai & Suburbs
    "400001": {"district": "Mumbai City", "state": "Maharashtra", "areas": ["Mumbai G.P.O.", "Fort"]},
    "400002": {"district": "Mumbai City", "state": "Maharashtra", "areas": ["Kalbadevi H.O."]},
    "400004": {"district": "Mumbai City", "state": "Maharashtra", "areas": ["Girgaon H.O."]},
    "400011": {"district": "Mumbai City", "state": "Maharashtra", "areas": ["Jacob Circle"]},
    "400012": {"district": "Mumbai City", "state": "Maharashtra", "areas": ["Parel"]},
    "400014": {"district": "Mumbai City", "state": "Maharashtra", "areas": ["Dadar H.O."]},
    "400049": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Juhu"]},
    "400050": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Bandra"]},
    "400051": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Bandra East", "BKC"]},
    "400058": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Andheri R.S."]},
    "400069": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Andheri East"]},
    "400076": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["I.I.T. Powai"]},
    "400080": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Mulund West"]},
    "400081": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Mulund East"]},
    "400091": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Borivali H.O."]},
    "400092": {"district": "Mumbai Suburban", "state": "Maharashtra", "areas": ["Borivali West"]},

    # Maharashtra - Pune
    "411001": {"district": "Pune", "state": "Maharashtra", "areas": ["Pune HO"]},
    "411002": {"district": "Pune", "state": "Maharashtra", "areas": ["Pune City H.O."]},
    "411004": {"district": "Pune", "state": "Maharashtra", "areas": ["Deccan Gymkhana"]},
    "411019": {"district": "Pune", "state": "Maharashtra", "areas": ["Chinchwad East"]},
    "411026": {"district": "Pune", "state": "Maharashtra", "areas": ["Bhosari I.E."]},
    "411028": {"district": "Pune", "state": "Maharashtra", "areas": ["Hadapsar"]},
    "411033": {"district": "Pune", "state": "Maharashtra", "areas": ["Chinchwadgaon"]},

    # Karnataka - Bengaluru
    "560001": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Bangalore GPO", "MG Road"]},
    "560002": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Bangalore City HO"]},
    "560003": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Malleswaram", "Malleswaaram West"]},
    "560004": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Basavangudi H.O."]},
    "560005": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Cox Town", "Fraser Town"]},
    "560008": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Ulsoor H.O", "Ulsoor Bazar", "Artillery Road Ulsoor"]},
    "560011": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Jayanagar 3rd Block", "Jayanagar Byrasandra", "Jayanagar Madhavan Park", "Jayanagar South", "Jayanagar Tilak Nagar"]},
    "560017": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["HAL Bangalore", "Bangalore Air Port"]},
    "560034": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Koramangala"]},
    "560038": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Indira Nagar (Bangalore)", "Commercial Complex V", "Bypappanahalli", "HAL -2 Stage"]},
    "560040": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Vijaya Nagar", "Vijaya Nagar East", "R.P.C.Layout North Vijaya Nagar"]},
    "560041": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Jayanagar"]},
    "560053": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Chikpet", "Chikpet Balepet", "Chikpet Belimutt Road", "Chikpet Cotton Pet"]},
    "560060": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Kengeri"]},
    "560075": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Jeevan Bheema Nagar", "Jeevan Bheema Nagar New Thippasandra", "New Thipasandra"]},
    "560078": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Jayaprakash Narayan Nagar", "JP Nagar Yelachenahalli"]},
    "560082": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Jayanagar 7th Block", "Jayanagar West", "Jayanagar Yediyur"]},
    "560083": {"district": "Bengaluru Urban", "state": "Karnataka", "areas": ["Bannergatta"]},

    # Tamil Nadu - Chennai
    "600001": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Chennai GPO", "Chennai Seven Wells", "Chennai Angappanaicken Street", "Chennai Flower Bazar", "Chennai Govt. Stanley Hospital", "Chennai Kothwal Market", "Chennai Mannady", "Chennai Mint Buildings", "Chennai Monegar ChoulTRY", "Chennai Muthialpet", "Chennai Port Trust Admn. Office", "Chennai Sambier Street", "Chennai Wal Tax Road"]},
    "600002": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Anna Road HO", "Anna Road South", "Govt. Estate", "Madras Elect. System"]},
    "600003": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Central Station (Chennai)", "Park Town (Chennai)", "Rippon Building (Chennai)"]},
    "600004": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Mylapore (Chennai)", "Luz Church Road", "Madras Vivekananda College", "Mandavalli", "Police Headquarters (Mylapore Chennai)", "Santhome"]},
    "600005": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Chepauk", "Krishnampet", "Madras Presidency College", "Madras University Buildings", "Pardhasaradhi Koil", "Triplicane"]},
    "600006": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Cathedral (Chennai)", "Chennai University", "Greames Road (Chennai)", "Shastri Bhavan (Chennai)", "Teynampet West (Chennai)"]},
    "600010": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Kilpauk (Chennai)", "Kilpauk Garden Colony", "Kilpauk Medical College", "Kilpauk West", "Medavakkm Tank Road", "New Avadi Road(Chennai)"]},
    "600017": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["T. Nagar", "Thyagaraya Nagar", "Thyagaraya Nagar South", "Hindi Prachar Sabha", "North Tyagaraya Nagar", "Panagal Park", "Usman Road"]},
    "600018": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Abiramapuram [Teynampet]", "Chamiers Road [Teynampet]", "Eldams Road [Teynampet]", "Madras Accountant General Office", "Teynampet [Chennai]", "Teynampet South"]},
    "600020": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Adyar", "Central Insit. Of Tech.", "Central Leather Research Inst.", "Gandhi Nagar (Adyar)", "Kasturba Nagar (Adayar)", "Sastry Nagar (Adyar)", "Theosophical Society"]},
    "600028": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Foreshore Estate", "Raja Annamalaipuram", "Raja Annamalaipuram Colony", "Ramakrishna Nagar"]},
    "600034": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Nungambakkam Bazar", "Nungambakkam High Road", "Nungambakkam(Chennai)", "Layala College"]},
    "600040": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Anna Nagar"]},
    "600083": {"district": "Chennai", "state": "Tamil Nadu", "areas": ["Ashok Nagar Chennai"]},

    # Telangana / Andhra Pradesh - Hyderabad
    "500001": {"district": "Hyderabad", "state": "Telangana", "areas": ["Hyderabad GPO", "Gandhi Bhavan", "Gunfoundry", "State Bank of Hyderabad", "State Bank of India"]},
    "500002": {"district": "Hyderabad", "state": "Telangana", "areas": ["Hyderabad Jubilee", "Mogalpura", "Motigalli"]},
    "500003": {"district": "Hyderabad", "state": "Telangana", "areas": ["Secunderabad", "Begumpet Police Lines", "Bhoiguda", "Gandhi Hospital", "Gandhinagar", "M.G. Road"]},
    "500004": {"district": "Hyderabad", "state": "Telangana", "areas": ["A.C.Guards", "A.G.'s Office", "Anandnagar", "Bazzarghat", "Shyamnagar"]},
    "500016": {"district": "Hyderabad", "state": "Telangana", "areas": ["Begumpet", "Hyderabad Airport 1", "Hyderabad Airport II", "Prakasam Nagar"]},
    "500028": {"district": "Hyderabad", "state": "Telangana", "areas": ["Ahmednagar", "Dattatreya Colony", "J.N.T.U.", "Shantinagar"]},
    "500029": {"district": "Hyderabad", "state": "Telangana", "areas": ["Asifnagar", "Gaganmahal", "Himayathnagar", "Parishram Bhavan", "R.K.Mutt."]},
    "500032": {"district": "Hyderabad", "state": "Telangana", "areas": ["Gachibowli"]},
    "500034": {"district": "Hyderabad", "state": "Telangana", "areas": ["Banjara Hills"]},
    "500038": {"district": "Hyderabad", "state": "Telangana", "areas": ["Sanjeevareddynagar", "Vengalraonagar"]},
    "500081": {"district": "Hyderabad", "state": "Telangana", "areas": ["Cyberabad", "Madhapur", "Hitec City"]},

    # Gujarat - Ahmedabad
    "380001": {"district": "Ahmedabad", "state": "Gujarat", "areas": ["Ahmedabad GPO", "Darianpur", "Gandhi Road", "Kalupur Chakla", "Manek Chowk", "Rai Khal", "Raipur", "Salapuz"]},
    "380006": {"district": "Ahmedabad", "state": "Gujarat", "areas": ["Ambavadi Gujrat College (Ellisbridge)", "Ellis Bridge"]},
    "380009": {"district": "Ahmedabad", "state": "Gujarat", "areas": ["Ashram Road (Navarang Pura)", "Navarang Pura HO"]},
    "380015": {"district": "Ahmedabad", "state": "Gujarat", "areas": ["Azad Society (Polytechnic)", "Indian Inst. Of Management", "Polytechnic"]},
    "380054": {"district": "Ahmedabad", "state": "Gujarat", "areas": ["Tal Tej Road", "Thaltej"]},

    # Gujarat - Surat
    "395001": {"district": "Surat", "state": "Gujarat", "areas": ["Athwa Lines (Surat Nanpura)", "Gopipura (Surat Nanpura)", "Govt. Medical College (Surat Nanpura)", "Surat Nanpura"]},
    "395002": {"district": "Surat", "state": "Gujarat", "areas": ["Indurpura (Surat Sagrampura Putli)", "Khatodra (Surat Sagrampura Putli)", "New Cloth Market", "Rustompura", "Sagrampura (Surat Sagrampura Putli)", "Surat Sagrampura Putli", "Textile Market"]},
    "395003": {"district": "Surat", "state": "Gujarat", "areas": ["Aganovad (Surat)", "Begumpura (Surat)", "Bhavaniyad (Surat)", "Bhagal (Surat)", "Jhampa (Surat)", "Muglisara (Surat)", "Nawabvadi (Surat)", "Nawabwadi (Surat)", "Sayedpura (Surat)", "Surat City", "Surat RS", "Variavi Bhagal (Surat)"]},
    "395006": {"district": "Surat", "state": "Gujarat", "areas": ["Surat Varachha Road", "Varachha"]},
    "395007": {"district": "Surat", "state": "Gujarat", "areas": ["Athwa (Surat SVR College)", "Surat S.V.R. College"]},

    # West Bengal - Kolkata
    "700001": {"district": "Kolkata", "state": "West Bengal", "areas": ["Kolkata GPO", "Dalhousie Square"]},
    "700006": {"district": "Kolkata", "state": "West Bengal", "areas": ["Beadon Street", "Simla"]},
    "700019": {"district": "Kolkata", "state": "West Bengal", "areas": ["Ballygunge"]},
    "700027": {"district": "Kolkata", "state": "West Bengal", "areas": ["Alipore HO"]},
    "700073": {"district": "Kolkata", "state": "West Bengal", "areas": ["Chittaranjan Avenue"]},
    "700091": {"district": "Kolkata", "state": "West Bengal", "areas": ["Salt Lake Sector V", "Sech Bhawan"]},
}

@router.get("/{pincode}", response_model=PincodeResponse)
async def lookup_pincode(pincode: str):
    """
    Lookup District, State, and Area/Post Offices by 6-digit Indian PIN code.
    1. Checks fast offline dictionary.
    2. Falls back to live postal service with caching.
    """
    pin = pincode.strip()
    if not (len(pin) == 6 and pin.isdigit()):
        raise HTTPException(status_code=400, detail="Invalid PIN code format. Must be 6 digits.")

    # 1. Cache hit
    if pin in _PIN_CACHE:
        return _PIN_CACHE[pin]

    # 2. Local builtin dataset hit
    if pin in _BUILTIN_PIN_DATA:
        data = _BUILTIN_PIN_DATA[pin]
        result = PincodeResponse(
            pincode=pin,
            district=data["district"],
            state=data["state"],
            areas=data.get("areas", [data["district"]]),
        )
        _PIN_CACHE[pin] = result
        return result

    # 3. Online fallback to India Post API
    try:
        url = f"https://api.postalpincode.in/pincode/{pin}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DRISHTI-LENS/1.0 (Public Healthcare System)"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                raw = json.loads(response.read().decode("utf-8"))
                if raw and isinstance(raw, list) and raw[0].get("Status") == "Success":
                    post_offices = raw[0].get("PostOffice", [])
                    if post_offices:
                        first = post_offices[0]
                        district = first.get("District", "")
                        state = first.get("State", "")
                        areas = [po.get("Name") for po in post_offices if po.get("Name")]
                        if not areas:
                            areas = [district]
                        result = PincodeResponse(
                            pincode=pin,
                            district=district,
                            state=state,
                            areas=areas,
                        )
                        _PIN_CACHE[pin] = result
                        return result
    except Exception as e:
        logger.warning(f"Live PIN lookup fallback failed for {pin}: {e}")

    # 4. Fallback: region heuristics based on first digit of PIN
    first_digit_map = {
        "1": ("Northern Region", "Delhi / Haryana / Punjab"),
        "2": ("Northern Region", "Uttar Pradesh / Uttarakhand"),
        "3": ("Western Region", "Rajasthan / Gujarat"),
        "4": ("Western Region", "Maharashtra / Goa / MP"),
        "5": ("Southern Region", "Andhra Pradesh / Telangana / Karnataka"),
        "6": ("Southern Region", "Tamil Nadu / Kerala"),
        "7": ("Eastern Region", "West Bengal / Odisha / NE"),
        "8": ("Eastern Region", "Bihar / Jharkhand"),
    }
    def_dist, def_state = first_digit_map.get(pin[0], ("District " + pin[:3], "India"))
    fallback_res = PincodeResponse(
        pincode=pin,
        district=def_dist,
        state=def_state,
        areas=[f"Area {pin}"],
    )
    _PIN_CACHE[pin] = fallback_res
    return fallback_res

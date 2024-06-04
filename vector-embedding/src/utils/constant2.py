prefixes="""PREFIX  com: <https://company.org/resource/>
PREFIX  owl: <http://www.w3.org/2002/07/owl#> 
PREFIX  xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX  rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX  dbr2: <https://dbpedia.org/resource/>
PREFIX  path: <http://www.ontotext.com/path#>
PREFIX  dbr3: <https://www.salesforce.com/company/>
PREFIX  dbr_scrap: <https://www.zeniagraphscrap.com/company/>
PREFIX  dbr1: <https://www.linkedin.com/company/>
PREFIX  yahoo: <https://finance.yahoo.com/quote/>
PREFIX  foaf: <http://xmlns.com/foaf/0.1/>
PREFIX  dbr_gkg: <https://www.zeniagraphgkg.com/company/>
PREFIX  vcard: <http://www.w3.org/2006/vcard/ns#>
PREFIX  pro: <http://property.org/resource/>
PREFIX  dbr4: <https://www.zoominfo.com/company/>
PREFIX  dbo: <http://dbpedia.org/ontology/>
PREFIX  node: <http://property.org/node/>
PREFIX  dbp: <http://dbpedia.org/property/>
PREFIX  rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  finance: <http://property.org/finance/>


"""



ontology='''
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dbp: <http://dbpedia.org/property/> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix com: <https://company.org/resource/> .
@prefix dbr1: <https://www.linkedin.com/company/> .
@prefix dbr2: <https://dbpedia.org/resource/> .
@prefix dbr3: <https://www.salesforce.com/company/> .
@prefix dbr_gkg: <https://www.zeniagraphgkg.com/company/> .
@prefix dbr_scrap: <https://www.zeniagraphscrap.com/company/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix pro: <http://property.org/resource/> .
@prefix node: <http://property.org/node/>.
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix yahoo: <https://finance.yahoo.com/quote/> .

dbo:Organisation a owl:Class .

dbo:Company a owl:Class .

dbo:Finance a owl:Class .

dbo:CustomProperty a owl:Class .

dbo:employer  rdf:type   rdf:Property,owl:ObjectProperty ;
              rdfs:domain dbo:Company ;
              rdfs:range  vcard:Individual .

dbo:source  a           rdf:Property ;
            rdfs:domain dbo:Organisation ;
            rdfs:range  dbo:Company,dbo:Finance .

dbp:name      rdf:type rdf:Property ;
              rdfs:domain dbo:Company,dbo:Finance  ;
              rdfs:range xsd:string .
			  
dbo:description  rdf:type rdf:Property ;
              rdfs:domain dbo:Company  ;
              rdfs:range xsd:string .
				  

dbo:naics  rdf:type owl:DatatypeProperty ;
           rdfs:domain  dbo:Company  ;
           rdfs:range xsd:integer .	   
             		 
dbo:sic rdf:type owl:DatatypeProperty ;
         rdfs:domain  dbo:Company  ;
         rdfs:range xsd:integer .	 
          
dbo:no_of_employees   rdf:type rdf:Property ;
	      rdfs:domain  dbo:Company,dbo:Finance  ;
              rdfs:range xsd:integer .
    
         	        
dbo:industry   rdf:type rdf:Property ;
	       rdfs:domain  dbo:Company,dbo:Finance  ;
              rdfs:range xsd:string .
                        
                                                
dbo:headquarters   rdf:type   rdf:Property ;
	        rdfs:domain  dbo:Company  ;
              rdfs:range xsd:string .


dbo:company_type   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
             		 rdfs:range rdfs:Literal .					 		  

foaf:operating_years   rdf:type rdf:Property ;
              rdfs:domain  dbo:Company  ;
              rdfs:range xsd:integer .
  
foaf:founded   rdf:type rdf:Property ;
              rdfs:domain  dbo:Company  ;
              rdfs:range xsd:integer .
					
	

foaf:timestamp  rdf:type owl:DatatypeProperty ;
                rdfs:domain dbo:Company .
				

dbo:score  rdf:type owl:DatatypeProperty ;
           rdfs:domain dbo:Company , dbo:Organisation .
		   
		   
foaf:social_url  rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
             		 rdfs:range rdfs:Literal .

foaf:wiki_url  rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
             		 rdfs:range rdfs:Literal .
         		 

foaf:Specialities   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
					 rdfs:range rdfs:Literal .
					 
foaf:parent_name   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company,dbo:Finance  ;
					 rdfs:range rdfs:Literal .
					 
foaf:custom_properties  rdf:type owl:DatatypeProperty ;
                       rdfs:domain  dbo:Company,dbo:Finance  ;
					   rdfs:range dbo:CustomProperty .

			
foaf:quarterly_revenue_growth rdf:type rdf:Property ;
                    rdfs:domain dbo:Finance  ;
			        rdfs:range xsd:float .
			
foaf:symbol rdf:type rdf:Property ;
            rdfs:domain dbo:Finance  ;
			rdfs:range rdfs:Literal .

foaf:exchange rdf:type rdf:Property ;
              rdfs:domain dbo:Finance  ;
			  rdfs:range rdfs:Literal .
			
foaf:current_year_revenue rdf:type rdf:Property ;
                         rdfs:domain dbo:Finance  ;
			rdfs:range xsd:integer .
						 
foaf:previous_year_revenue rdf:type rdf:Property ;
                         rdfs:domain dbo:Finance  ;
			rdfs:range xsd:integer .
foaf:total_assets rdf:type rdf:Property ;
                  rdfs:domain dbo:Finance  ;
		rdfs:range xsd:integer .	
				  
foaf:gross_profit rdf:type rdf:Property ;
                  rdfs:domain dbo:Finance  ;
		rdfs:range xsd:integer .	
				  
foaf:website rdf:type rdf:Property ;
             rdfs:domain dbo:Finance  ;
	     rdfs:range rdfs:Literal .	
			 
foaf:market_cap rdf:type rdf:Property ;
                rdfs:domain dbo:Finance  ;
		rdfs:range xsd:integer .
				
foaf:last_quarterly_revenue rdf:type rdf:Property ;
                            rdfs:domain dbo:Finance  ;
			rdfs:range xsd:integer .
						 
foaf:second_last_quarterly_revenue rdf:type rdf:Property ;
                                   rdfs:domain dbo:Finance  ;
				 rdfs:range xsd:integer .
								   	
foaf:long_business_summary	 rdf:type rdf:Property ;
              rdfs:domain dbo:Finance  ;
	rdfs:range rdfs:Literal .			   
			  			     
 '''

sample_rdf_data='''
@prefix dbp: <http://dbpedia.org/property/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dbr1: <https://www.linkedin.com/company/> .
@prefix com: <https://company.org/resource/> .
@prefix pro: <http://property.org/resource/> .
@prefix node: <http://property.org/node/> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .



dbr2:Microsoft a dbo:Company;
  dbp:name "Microsoft Corporation";
  dbo:industry "Information_technology";
  dbo:headquarters "Microsoft_Redmond_campus", "Redmond,_Washington";
  dbo:no_of_employees 221000;
  dbo:company_type "Public_company";
  foaf:founded "1975-04-04"^^xsd:date;
  rdfs:label "Microsoft Corporation_DBPedia";
  dbo:description "Microsoft Corporation is an American multinational technology corporation producing computer software, consumer electronics, personal computers, and related services headquartered at the Microsoft Redmond campus located in Redmond, Washington, United States. Its best-known software products are the Windows line of operating systems, the Microsoft Office suite, and the Internet Explorer and Edge web browsers. Its flagship hardware products are the Xbox video game consoles and the Microsoft Surface lineup of touchscreen personal computers. Microsoft ranked No. 21 in the 2020 Fortune 500 rankings of the largest United States corporations by total revenue; it was the world's largest software maker by revenue as of 2019. It is one of the Big Five American information technology companies, alongside Alphabet, Amazon, Apple, and Meta. Microsoft was founded by Bill Gates and Paul Allen on April 4, 1975, to develop and sell BASIC interpreters for the Altair 8800. It rose to dominate the personal computer operating system market with MS-DOS in the mid-1980s, followed by Windows. The company's 1986 initial public offering (IPO), and subsequent rise in its share price, created three billionaires and an estimated 12,000 millionaires among Microsoft employees. Since the 1990s, it has increasingly diversified from the operating system market and has made a number of corporate acquisitions, their largest being the acquisition of LinkedIn for $26.2 billion in December 2016, followed by their acquisition of Skype Technologies for $8.5 billion in May 2011. As of 2015, Microsoft is market-dominant in the IBM PC compatible operating system market and the office software suite market, although it has lost the majority of the overall operating system market to Android. The company also produces a wide range of other consumer and enterprise software for desktops, laptops, tabs, gadgets, and servers, including Internet search (with Bing), the digital services market (through MSN), mixed reality (HoloLens), cloud computing (Azure), and software development (Visual Studio). Steve Ballmer replaced Gates as CEO in 2000, and later envisioned a \"devices and services\" strategy. This unfolded with Microsoft acquiring Danger Inc. in 2008, entering the personal computer production market for the first time in June 2012 with the launch of the Microsoft Surface line of tablet computers, and later forming Microsoft Mobile through the acquisition of Nokia's devices and services division. Since Satya Nadella took over as CEO in 2014, the company has scaled back on hardware and has instead focused on cloud computing, a move that helped the company's shares reach its highest value since December 1999. Earlier dethroned by Apple in 2010, in 2018 Microsoft reclaimed its position as the most valuable publicly traded company in the world. In April 2019, Microsoft reached the trillion-dollar market cap, becoming the third U.S. public company to be valued at over $1 trillion after Apple and Amazon respectively. As of 2022, Microsoft has the fourth-highest global brand valuation. Microsoft has been criticized for its monopolistic practices and the company's software has been criticized for problems with ease of use, robustness, and security.";
  foaf:custom_properties <http://property.org/resource/Microsoft%20Corporation_DBPedia_Properties>;
  foaf:parent_name "Microsoft Corporation";
  foaf:profile_url "http://dbpedia.org/resource/Microsoft";
  dbo:source "dbpedia" .
  rdfs:label "Microsoft Corporation_Finance";
  dbo:industry "Software—Infrastructure";
  foaf:quarterly_revenue_growth "0.083"^^xsd:float;
  foaf:ticker-symbol "MSFT-NMS";
  foaf:current_year_revenue 211915000000;
  foaf:previous_year_revenue 198270000000;
  foaf:total_assets 411976000000;
  foaf:gross_profit 146052000000;
  dbo:no_of_employees 221000;
  foaf:website "www.microsoft.com";
  foaf:market_cap 2401142571008;
  foaf:last_quarterly_revenue 56189000000;
  foaf:second_last_quarterly_revenue 52857000000;
  foaf:long_business_summary "Microsoft Corporation develops and supports software, services, devices and solutions worldwide. The Productivity and Business Processes segment offers office, exchange, SharePoint, Microsoft Teams, office 365 Security and Compliance, Microsoft viva, and Microsoft 365 copilot; and office consumer services, such as Microsoft 365 consumer subscriptions, Office licensed on-premises, and other office services. This segment also provides LinkedIn; and dynamics business solutions, including Dynamics 365, a set of intelligent, cloud-based applications across ERP, CRM, power apps, and power automate; and on-premises ERP and CRM applications. The Intelligent Cloud segment provides server products and cloud services, such as azure and other cloud services; SQL and windows server, visual studio, system center, and related client access licenses, as well as nuance and GitHub; and enterprise services including enterprise support services, industry solutions, and nuance professional services. The More Personal Computing segment offers Windows, including windows OEM licensing and other non-volume licensing of the Windows operating system; Windows commercial comprising volume licensing of the Windows operating system, windows cloud services, and other Windows commercial offerings; patent licensing; and windows Internet of Things; and devices, such as surface, HoloLens, and PC accessories. Additionally, this segment provides gaming, which includes Xbox hardware and content, and first- and third-party content; Xbox game pass and other subscriptions, cloud gaming, advertising, third-party disc royalties, and other cloud services; and search and news advertising, which includes Bing, Microsoft News and Edge, and third-party affiliates. The company sells its products through OEMs, distributors, and resellers; and directly through digital marketplaces, online, and retail stores. The company was founded in 1975 and is headquartered in Redmond, Washington.";
  foaf:parent_name "Microsoft Corporation";
  dbo:source "yahoo_finance" .
	'''


claims_ontology = '''# Define the Namespace
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <http://example.org/insurance#> .
@prefix person: <http://insurance.org/individual/> .
@prefix claim: <http://insurance.org/claim/> .
@prefix policy: <http://insurance.org/policy/> .
@prefix vehicle: <https://vehicle.org/auto/VC/> .
@prefix policyPlan: <http://insurance.org/policyPlan/> .


# Ontology Definition
:InsuranceOntology rdf:type owl:Ontology ;
    rdfs:comment "An ontology representing insurance policies, claims, vehicles, and persons." .

# Classes
:Policy rdf:type owl:Class ;
    rdfs:comment "Represents an insurance policy." .

:AutoInsurance rdf:type owl:Class ;
     rdfs:subClassOf :Policy ;
     rdfs:comment "Represents a Auto mobile insurance policy." .

:MotorcycleInsurance rdf:type owl:Class ;
     rdfs:subClassOf :Policy ;
     rdfs:comment "Represents a MotorcycleInsurance policy." .

:BoatInsurance rdf:type owl:Class ;
     rdfs:subClassOf :Policy ;
     rdfs:comment "Represents a BoatInsurance policy." .

:CommercialVehicleInsurance rdf:type owl:Class ;
     rdfs:subClassOf :Policy ;
     rdfs:comment "Represents a CommercialVehicleInsurance policy." .

:ClassicCarInsurance rdf:type owl:Class ;
     rdfs:subClassOf :Policy ;
     rdfs:comment "Represents a ClassicCarInsurance policy." .



:Claim rdf:type owl:Class ;
    rdfs:comment "Represents an insurance claim." .

:AutoInsuranceClaim rdf:type owl:Class ;
    rdfs:subClassOf :Claim ;
    rdfs:comment "Represents a claim related to an Auto " .

:MotorcycleInsuranceClaim rdf:type owl:Class ;
    rdfs:subClassOf :Claim ;
    rdfs:comment "Represents a claim related to a Motorcycle" .

:BoatInsuranceClaim rdf:type owl:Class ;
    rdfs:subClassOf :Claim ;
    rdfs:comment "Represents a claim related to a BoatInsurance." .

:CommercialVehicleInsuranceClaim rdf:type owl:Class ;
    rdfs:subClassOf :Claim ;
    rdfs:comment "Represents a claim related to a CommercialVehicle." .

:ClassicCarInsuranceClaim rdf:type owl:Class ;
    rdfs:subClassOf :Claim ;
    rdfs:comment "Represents a claim related to a ClassicCar." .



:Vehicle rdf:type owl:Class ;
    rdfs:comment "Represents a vehicle to be insured." .

:Person rdf:type owl:Class ;
    rdfs:comment "Represents an individual." .

:PolicyPlan rdf:type owl:Class ;
    rdfs:comment "Represents a Policy Plan" .


# Object Properties
:policy rdf:type owl:ObjectProperty ;
    rdfs:domain :Claim ;
    rdfs:range :Policy ;
    rdfs:comment "Relates a policy to its associated claims." .

:insured rdf:type owl:ObjectProperty ;
     rdfs:domain :Claim ;
     rdfs:range :Person ;
     rdfs:comment "Relates a claim to the insured entity it belongs to." .

:ownerOfVehicle rdf:type owl:ObjectProperty ;
    rdfs:domain :Vehicle ;
    rdfs:range :Person ;
    rdfs:comment "Relates a person to the vehicles they own." .

:policyHolder rdf:type owl:ObjectProperty ;
    rdfs:domain :Policy ;
    rdfs:range :Person ;
    rdfs:comment "Policy Holder for a policy." .

:policyPlan rdf:type owl:ObjectProperty ;
    rdfs:domain :Policy ;
    rdfs:range :PolicyPlan ;
    rdfs:comment "Policy Plan for a policy." .



# Data Properties
#Policy

:policyNumber rdf:type owl:DatatypeProperty ;
    rdfs:domain :Policy ;
    rdfs:comment "Unique identifier for a policy." .

:coverageStartDate rdf:type owl:DatatypeProperty ;
    rdfs:domain :Policy ;
    rdfs:comment "Start date of insurance coverage." .

:coverageEndDate rdf:type owl:DatatypeProperty ;
    rdfs:domain :Policy ;
    rdfs:comment "End date of insurance coverage." .

:premiumAmount rdf:type owl:DatatypeProperty ;
    rdfs:domain :Policy ;
    rdfs:comment "Premium Amount for a policy" .

:policyTerm rdf:type owl:DatatypeProperty ;
    rdfs:domain :Policy ;
    rdfs:comment "Policy Term for a policy" .

:policyPremiumTerm rdf:type owl:DatatypeProperty ;
    rdfs:domain :Policy ;
    rdfs:comment "Policy Premium Term for a policy" .

:hasVehicleCovered rdf:type rdf:Property ;
    rdfs:domain :Policy ;
    rdfs:range :Vehicle .

#Claim
:claimID rdf:type owl:DatatypeProperty ;
    rdfs:domain :Claim ;
    rdfs:comment "Unique identifier for a claim." .
:claimDate rdf:type owl:DatatypeProperty ;
    rdfs:domain :Claim ;
    rdfs:comment "Date when a claim is filed." .
:claimStatus rdf:type owl:DatatypeProperty ;
    rdfs:domain :Claim ;
    rdfs:comment "Status of the insurance claim (e.g., pending, approved)." .
:claimStatusReason rdf:type owl:DatatypeProperty ;
    rdfs:domain :Claim ;
    rdfs:comment "Reason of status of insurance claim. " .
:claimAmount rdf:type owl:DatatypeProperty ;
    rdfs:domain :Claim ;
    rdfs:comment "Amount claimed in the insurance claim." .
:claimDescription rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:comment "Claim Description." .

:incidentDate rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:range xsd:date .

:incidentTime rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:range xsd:time .

:incidentLocation rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:range xsd:string .

:incidentType rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:range xsd:string .

:incidentDescription rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:range xsd:string .

:vehicle rdf:type rdf:Property ;
    rdfs:domain :Claim ;
    rdfs:range :Vehicle .

:adjusterNotes rdf:type rdf:Property ;
    rdfs:domain :Claim .

:witnessInformation rdf:type rdf:Property ;
    rdfs:domain :Claim .

:injuryInformation rdf:type rdf:Property ;
    rdfs:domain :Claim .

:claimTitle rdf:type rdf:Property ;
    rdfs:domain :Claim .

#Vehicle
:vin rdf:type owl:DatatypeProperty ;
    rdfs:domain :Vehicle ;
    rdfs:comment "Unique identifier for a vehicle." .
:licensePlate rdf:type owl:DatatypeProperty ;
    rdfs:domain :Vehicle ;
     rdfs:comment "vehicle Registration Number(license plate)" .
:vehicleType rdf:type owl:DatatypeProperty ;
    rdfs:domain :Vehicle ;
    rdfs:comment "Type of vehicle (e.g., car, motorcycle)." .
:model rdf:type owl:DatatypeProperty ;
    rdfs:domain :Vehicle ;
    rdfs:comment "Model of the vehicle." .
:year rdf:type owl:DatatypeProperty ;
    rdfs:domain :Vehicle ;
    rdfs:comment "Manufacturing year of the vehicle." .

#Person
:personID rdf:type owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:comment "Unique identifier for a person." .
:personName rdf:type owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:comment "Name of the individual." .
:personAddress rdf:type owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:comment "Address of the individual." .
:personContactDetails rdf:type owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:comment "Contact details of the individual." .

policyPlan:ComprehensiveCoverage rdf:type :PolicyPlan ;
                   :policyProvider "Assurant";
                   :policyPlanName "ComprehensiveCoveragePlan";
                   :policyPlanDescription  "It likely covers all types of damages or losses not specifically excluded in the policy, including theft, vandalism, fire, and natural disasters. This is a broad policy offering wide-ranging protection." .

policyPlan:CollisionCoverage rdf:type :PolicyPlan ;
                   :policyProvider "Assurant";
                   :policyPlanName "CollisionCoveragePlan";
                   :policyPlanDescription  "it's a collision with another vehicle or an object, this plan typically pays for the repair or replacement of the insured vehicle." .

policyPlan:LiabilityInsurance rdf:type :PolicyPlan ;
                   :policyProvider "Assurant";
                   :policyPlanName "LiabilityInsuranceplan";
                   :policyPlanDescription  "This generally includes coverage for bodily injury and property damage that the policyholder is found legally responsible for following an accident. It's a fundamental coverage often required by law." .




'''
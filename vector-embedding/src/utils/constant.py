prefixes="""PREFIX owl: <http://www.w3.org/2002/07/owl#> 
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX dbp: <http://dbpedia.org/property/> 
PREFIX dbo: <http://dbpedia.org/ontology/> 
PREFIX com: <https://company.org/resource/> 
PREFIX dbr1: <https://www.linkedin.com/company/> 
PREFIX dbr2: <https://dbpedia.org/resource/> 
PREFIX dbr3: <https://www.salesforce.com/company/> 
PREFIX dbr_gkg: <https://www.zeniagraphgkg.com/company/> 
PREFIX dbr_scrap: <https://www.zeniagraphscrap.com/company/> 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX pro: <http://property.org/resource/> 

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


dbo:source a rdf:Property ;
    rdfs:domain dbo:Organisation ;
    rdfs:range dbo:Company .

dbp:name      rdf:type rdf:Property ;
              rdfs:domain dbo:Company  ;
              rdfs:range xsd:string .

dbo:numberOfEmployees   rdf:type rdf:Property ;
			rdfs:domain  dbo:Company   ;
              rdfs:range xsd:integer .

dbo:industry   rdf:type rdf:Property ;
	       rdfs:domain  dbo:Company   ;
          rdfs:range xsd:string .

dbo:location   rdf:type rdf:Property ;
               rdfs:domain  dbo:Company   ;
              rdfs:range xsd:string .
  
dbo:headquarter   rdf:type   rdf:Property ;
	        rdfs:domain  dbo:Company   ;
              rdfs:range xsd:string .
  
dbp:founded   rdf:type rdf:Property ;
              rdfs:domain  dbo:Company   ;
              rdfs:range xsd:integer .

foaf:annualgrowth  rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company   ;
              rdfs:range xsd:double .

foaf:quaterlygrowth  rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:double .

foaf:WebsiteUrl  rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:string .

foaf:companyType   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company   ;
              rdfs:range xsd:string .

foaf:yearlyRevenue2022   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company ;
              rdfs:range xsd:integer .
             		

foaf:yearlyRevenue2021   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company ;
              rdfs:range xsd:integer .
             		 

foaf:lastQuarterlyRevenue   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company ;
              rdfs:range xsd:integer .
             		 

foaf:secondQuarterlyRevenue   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:integer .
             		 

foaf:sales   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:integer .
             		 

foaf:profit   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company ;
              rdfs:range xsd:integer .
             		

foaf:assets   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:integer .
             		 

foaf:description   rdf:type owl:DatatypeProperty ;
                   rdfs:domain  dbo:Company  ;
              rdfs:range xsd:string .

foaf:Specialities   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:string .

             		 
foaf:SocialFollowers   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
             		 rdfs:range xsd:integer .

foaf:SocialURL   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:string .

foaf:CompaniesSize  rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  ;
              rdfs:range xsd:string .

foaf:MarketValue   rdf:type owl:DatatypeProperty ;
               		 rdfs:domain  dbo:Company  .
             		 
foaf:manual  rdf:type owl:DatatypeProperty ;
                     rdfs:domain  dbo:Company  .

foaf:customProperties  rdf:type owl:DatatypeProperty ;
                        rdfs:domain  dbo:Company  .

dbo:NAICS  rdf:type owl:DatatypeProperty ;
           rdfs:domain  dbo:Company  ;
           rdfs:range xsd:integer .
             		 
dbo:SIC  rdf:type owl:DatatypeProperty ;
         rdfs:domain  dbo:Company  ;
         rdfs:range xsd:integer .

dbo:score  rdf:type owl:DatatypeProperty ;
           rdfs:domain dbo:Company .
           
foaf:timestamp  rdf:type owl:DatatypeProperty ;
                rdfs:domain dbo:Company .
           
 '''

sample_data='''@base <http://example.com/base/> .
@prefix dbp: <http://dbpedia.org/property/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dbr1: <https://www.linkedin.com/company/> .
@prefix com: <https://company.org/resource/> .
@prefix pro: <http://property.org/resource/> .

dbr1:Berkshire-Hathaway a dbo:Company;
  dbp:name "Berkshire-Hathaway";
  dbo:industry "Insurance";
  dbo:headquarter "U.S.A";
  dbo:location "United States";
  foaf:quarterlygrowth 9.29E0;
  foaf:annualgrowth 9.37E0;
  dbo:numberOfEmployees 7732;
  foaf:companyType "Public Company";
  dbp:founded 1939;
  foaf:WebsiteUrl "http://www.berkshirehathaway.com";
  foaf:assets 958780000000;
  foaf:sales 276090000000;
  foaf:profit 89800000000;
  foaf:yearlyRevenue2022 302089000000;
  foaf:yearlyRevenue2021 276203000000;
  foaf:lastQuarterlyRevenue 85393000000;
  foaf:secondQuarterlyRevenue 78132000000;
  rdfs:label "Berkshire-Hathaway_LinkedIn";
  dbo:abstract "Berkshire Hathaway Inc. is an American multinational conglomerate holding company headquartered in Omaha, Nebraska, United States. ";
  dbo:SIC 6719;
  dbo:NAICS 551112;
  foaf:SocialURL "https://www.linkedin.com/company/berkshire-hathaway";
  foaf:CompaniesSize "10001+" .

com:Berkshire-Hathaway a dbo:Organisation;
  dbo:source dbr1:Berkshire-Hathaway .'''
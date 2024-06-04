from argparse import Namespace
import time
import networkx as nx
from rdflib import Graph, RDF, URIRef,Namespace,Literal
import requests
import urllib.parse as urllp
from difflib import SequenceMatcher
import schedule
import threading
import unicodedata
from pydantic import BaseModel
import os 
from dotenv import load_dotenv

load_dotenv()

# .________________________________________________________    GLOBAL VARIABLES_________________________________________________________________________________
# Create an RDF graph and load your data
rdf_graph = Graph()
positions = {'CEO':0.001,'COO':0.002,'CIO':0.003,'Founder':0.4,'President':0.5,'Director':2,'Chief':4,'Manager':6,'Senior':8}
schedular_started = False

# Graph DB endpoints
GRAPHDB_SERVICE = os.getenv("GRAPHDB_SERVICE")

# GraphDB Instance Username and Password
GRAPHDB_USERNAME = 'admin'
GRAPHDB_PASSWORD = 'root' #'root'
# Default GraphDB Repository Name
DEFAULT_GRAPHDB_REPO = "MASTER-REPO-V2"
GRAPHDB_LOGIN = GRAPHDB_SERVICE + '/rest/login'
# .________________________________________________________    GLOBAL VARIABLES ENDS_________________________________________________________________________________
#  PYHTON CODE TO CONNECT TO MASTER REPO TO GET UPDATED TTL FILE..................START HERE....................................
def encodeURIComponent(s): return urllp.quote(
    s, safe='/', encoding=None, errors=None)



def login():
    results = {}
    obj = {
        "username": GRAPHDB_USERNAME,
        "password": GRAPHDB_PASSWORD
    }
    headers = {"Content-Type": "application/json",
               "Access-Control-Expose-Headers": "*"}
    try:
        response = requests.post(GRAPHDB_LOGIN, json=obj, headers=headers)
        if response.status_code == 200:
            results['token'] = response.headers['authorization']
        else:
            raise Exception("GraphDB unable to handle request!")
    except Exception as e:
        print("Exceptions Occured while logging graphDB")

    return results


def execute_data_query(params: dict):
    response = {'error': None, 'result': None}
    url = f"{GRAPHDB_SERVICE}/repositories/{params['repositoryID']}/rdf-graphs/service?default"
    print("Getting data from....",url)
    headers = {
        'Authorization': params['token'],
        'Accept': 'text/turtle'
    }
    try:
        resp = requests.request("GET", url, headers=headers)
        if resp.status_code == 200:
            print("Data retrieved !")
            response['result'] = resp.content
        else:
            print("No data Found")
            response['error'] = "Data not found"
    except Exception as e:
        response['error'] = e
    return response

# Main Calling Function to get Current TTL file from given repo
def get_current_data_from_graph():
    global schedular_started
    if schedular_started:
        schedular_started = False
        graphdb_login=login()
        passing_dict = {"repositoryID": DEFAULT_GRAPHDB_REPO, "token": graphdb_login.get('token')}
        statements = execute_data_query(passing_dict)
        if statements['result']:
            file_path = 'data/current_data.ttl'
            with open(file_path, "wb") as f:
                f.write(statements['result'])
                print(f"Data saved to {file_path}")
        return statements

lock = threading.Lock()

def job():
    global schedular_started
    schedular_started = True
    with lock:
        print("Running schedular")
        # Get the latest TTL file from GraphDB and save it locally
        result = get_current_data_from_graph()
        if result:
            load_graph_data()
            print("Successfully retrieved and saved the TTL file.")
        else:
            print("Failed to retrieve the TTL file:", result.get("error"))
    
def schedular_thread():
    # Schedule the job to run every morning at 8:00 AM
    schedule.every().day.at("08:00").do(job) 
    print("called Thread")
    while True: 
        # Infinite loop to run the scheduler continuously
        schedule.run_pending()
        time.sleep(30)  # Wait for 60 seconds before checking again


t1 = threading.Thread(target=schedular_thread,name='schedular_thread')
t1.start()
#  PYHTON CODE TO CONNECT TO MASTER REPO TO GET UPDATED TTL FILE..................ENDS HERE....................................
# .________________________________________________________   PARSING FUNCTIONS  FOR RDF-GRAPH_________________________________________________________________________________

# functions to load the current graph data
def load_graph_data():
    global rdf_graph
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
     
    data = parent_directory + '/data/current_data.ttl'
    try:
        rdf_graph.parse(data,format='turtle')
        print('Graph Loaded Successfully !!')
        create_graph_connections('experience')
        create_graph_connections('connections')
        create_graph_connections('skills')
        create_graph_connections('higher_level_friend')
        create_graph_connections('nearest_friend')
    except Exception as e:
        print("all other errors ignored",e)

# Function to remove unicodes
# input - string containing unicode characters
# retrurn - filtered string 
def remove_non_printable_chars(text):
    return ''.join(char for char in text if unicodedata.category(char)[0] != 'C')


# function to filter strings for subject
# Input - string containing -,_ at the end
# Output - Filtered String after removing -,_ from end
def remove_special_char(subject):
    sub = subject
    if str(sub).endswith('-') or str().endswith('_'):
        sub = sub[:-1]
        sub = remove_special_char(sub)
    return sub


# This function takes input as the mixed uri and converts it into multiple subjects
# Input- Mixed uri containing person name,company name,etc.
# Output- List of all subjects that existed in the mix uri
def clean_sub(sub_uri):
    subjects= []
    sub_uri = str(sub_uri).replace('ExperienceDetails','').replace('Experinecedetails','')
    sub_list= str(sub_uri).split('htt')
    for fea in sub_list:
        if fea:
            regex = remove_special_char(fea)
            subjects.append('htt'+str(regex))
    return subjects


# this functions iterates over all the roles in our graph and finds out the person role in a specific Company
# Input - person(URI of person to be searched)
# Output- String containing person role
def get_person_role(exp_uri):
    global rdf_graph
    for trip in rdf_graph.triples((URIRef(exp_uri),None,None)):
        if str(trip[1]) == 'http://dbpedia.org/ontology/role':
            return str(trip[2])


# This Filterting funtion that extracts company from mixed uri
# Input - Experience URI (URI of person to be searched,URI of the company) :String
# Output- Company hidden in that string :String
def get_company_from_one_uri(mixed_uri):
    company = None
    COMPANY = Namespace('http://dbpedia.org/ontology/')
    for trip in rdf_graph.triples((URIRef(mixed_uri),None,None)):
        if 'worked_in' in trip[1]:
            our_label = find_label_from_uri(str(trip[2]).replace('_WorkExperience',''))
            for comp in rdf_graph.subjects(RDF.type,COMPANY.Company):
                label = find_label_from_uri(comp)
                if label == our_label:
                    company = comp
                    break
    return company


def find_company_from_graph(comp_uri):
    COMPANY = Namespace('http://dbpedia.org/ontology/')
    for new_com in rdf_graph.subjects(RDF.type,COMPANY.Company):
        if str(comp_uri).startswith(new_com):
            return new_com
    for new_com in rdf_graph.subjects(RDF.type,COMPANY.Organisation):
        if str(comp_uri).startswith(new_com):
            return new_com
    return comp_uri


def find_all_people_in_company(company):
    company_edges = rdf_graph.triples((URIRef(company),None,None))
    people_list =[]
    for edges in company_edges:
        if str(edges[1]).endswith('/ontology/employees'):
            employees = list(rdf_graph.triples((edges[2],None,None))) + list(rdf_graph.triples((None,None,edges[2])))
            for emp in employees:
                if 'employee' in str(emp[1]) and not str(emp[2]).endswith('_Employments'):
                    people_list.append(str(emp[2]))
    return people_list


def find_label_from_uri(subject_uri):
    global rdf_graph
    for trip in rdf_graph.triples((URIRef(subject_uri),None,None)):
        if 'label' in str(trip).lower():
            return str(trip[2]).replace('_LinkedIn','')
    return 'None'

# .________________________________________________________    PARSING FUNCTIONS FOR NX-GRAPH   _________________________________________________________________________________
def load_nx_graph(connection_type):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    file_name = parent_directory + '/data/' +str(connection_type) + '_nx_graph.gexf'
    nx_graph = nx.read_gexf(file_name)
    print("Graph Loaded for ",connection_type)
    return nx_graph

# Function to find out label from uri
def find_label_from_nx_graph(person_uri,nx_graph):
    for id,label in nx.get_node_attributes(nx_graph,"label").items():
        if str(id) == str(person_uri):
            return label


# This Function is for bessermar use case and it finds out uri from label
def find_nxGraph_uri(person_name,nx_graph):
    person_tokens = str(person_name).split(' ')
    matched_dict = {}
    for id,_ in nx.get_node_attributes(nx_graph,"label").items():
        count = 0
        for token in person_tokens:
            if str(token).lower() in str(id).lower():
                count+=1
        if count > 0:
            matched_dict[id] = count
    if matched_dict:
        return max(zip(matched_dict.values(), matched_dict.keys()))[1]
    else:
        return None

# Company Person Shortest Path funtion
# finds out uri from label
def find_uri_from_nxlabel(target,nx_graph):
    for node,data in nx_graph.nodes(data=True):
        if str(data['label']).lower().replace(' ','') == str(target).lower().replace(' ',''):
            return str(node)


def findall_current_nx_graph_employees(person_uri,nx_graph):
    output_dict = {}
    for id, node in nx_graph.nodes(data=True):
        if 'employees' in node:
            employees = node['employees'].split("||")
            for emp in employees:
                if emp == person_uri:
                    output_dict['company'] = id
                    output_dict['employees'] = employees
                    print("Current company : ",id)
                    return output_dict
    else:
        print("Can't find this person ",person_uri)
        return None

# This function finds out the type of node passd for the URI
# INPUT- string:URI whose type you want to know
# OUTPUT - string:TYPE of URI
def get_type_of_node(sub_uri,seach_graph):
    for id,node in seach_graph.nodes(data=True):
        if id == sub_uri:
            if 'employees' in node:
                return 'company'
            else:
                return 'person'

def get_labelled_path(result_path,our_graph):
    labeled_path = []
    for i in range(0,len(result_path)-1,2):
        ob_dict = {}
        type_key = get_type_of_node(result_path[i],our_graph)
        ob_dict[type_key] = find_label_from_nx_graph(result_path[i],our_graph)
        ob_dict[type_key+"_uri"] = str(result_path[i])
        type_key = get_type_of_node(result_path[i+1],our_graph)
        ob_dict[type_key] = find_label_from_nx_graph(result_path[i+1],our_graph)
        ob_dict[type_key+"_uri"] = str(result_path[i+1])
        labeled_path.append(ob_dict)
    return labeled_path

# _____________________________________________ Create GRAPH CONNECTIONS FROM RDF TO NX__________________________________________________

def create_graph_connections(connection_type):
    global rdf_graph
    print("Creating connections")
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    
    if connection_type == "connections":
        connection_graph = nx.Graph()
        for s,p,o in rdf_graph:
            if "knows" in str(p).lower():
                for trip in rdf_graph.triples((URIRef(o),None,None)):
                    if "connection" in trip[1]:
                        connection_graph.add_node(remove_non_printable_chars(s),label=remove_non_printable_chars(find_label_from_uri(s)))
                        connection_graph.add_node(remove_non_printable_chars(trip[2]),label=remove_non_printable_chars(find_label_from_uri(str(trip[2]))))
                        connection_graph.add_edge(remove_non_printable_chars(s),remove_non_printable_chars(trip[2]))
        print("Connections completed according to ",connection_type," !! ")
        # Save the graph to a file
        
        file_name = parent_directory + '/data/' +str(connection_type) + '_nx_graph.gexf'
        nx.write_gexf(connection_graph,file_name)
        print("saved graph for ",connection_type,len(connection_graph))
    elif connection_type == "experience":
        exp_graph = nx.Graph()
        connections = set()
        for s,p,o in rdf_graph:
            if 'experiences' in p:
                for trip1 in rdf_graph.triples((URIRef(o),None,None)):
                    for trip2 in rdf_graph.triples((URIRef(trip1[2]),None,None)):
                        if 'label' in trip2[1]:
                            comp_name = trip2[2].replace('_WorkExperience','').replace('-ExperienceDetails','').replace('_ExperienceDetails','')
                            connections.add((remove_non_printable_chars(comp_name),remove_non_printable_chars(str(s))))
        for con in connections:
            exp_graph.add_edge(con[0],con[1])
        file_name = parent_directory + '/data/' +str(connection_type) + '_nx_graph.gexf'
        nx.write_gexf(exp_graph,file_name) 
        print("saved graph for ",connection_type,len(exp_graph))
    elif connection_type == 'skills':
        skill_graph = nx.Graph()
        connections = set()
        for s,p,o in rdf_graph:
            if 'skills' in str(p).lower():
                for trip1 in rdf_graph.triples((o,None,None)):
                    for trip2 in rdf_graph.triples((trip1[2],None,None)):
                        if 'skill' in str(trip2[1]):
                            connections.add((remove_non_printable_chars(str(trip2[2])),remove_non_printable_chars(str(s))))
        for con in connections:
            skill_graph.add_edge(con[0],con[1])
        print("Connections completed according to ",connection_type," !! ")
        file_name = parent_directory + '/data/' +str(connection_type) + '_nx_graph.gexf'
        nx.write_gexf(skill_graph,file_name,encoding='utf-16') 
        print("saved graph for ",connection_type,len(skill_graph))
    elif connection_type == "nearest_friend":
        friend_graph = nx.Graph()
        connections = set()
        for s, p, o in rdf_graph:
            if str(p) =='http://www.w3.org/2006/vcard/ns#experiences':
                for trip in rdf_graph.triples((URIRef(o),None,None)):
                    if 'experience_details' in str(trip[1]):
                        subs = clean_sub(str(trip[2]))
                        if len(subs) >= 2:
                            comp_uri = find_company_from_graph(subs[1])
                            connections.add((comp_uri, s))
                        else:
                            comp = get_company_from_one_uri(subs[0])
                            connections.add((comp, s))
        for con in connections:
            friend_graph.add_edge(con[0],con[1])
        for node in friend_graph.nodes():
            if "https://www.linkedin.com/in" in node or "http://example.org/candid/" in node:
                friend_graph.nodes[node]['label'] = remove_non_printable_chars(find_label_from_uri(node))
            else:
                friend_graph.nodes[node]['label'] = remove_non_printable_chars(find_label_from_uri(node))
                friend_graph.nodes[node]['employees'] = '||'.join(find_all_people_in_company(node))
        print("Connections completed !!",len(friend_graph))
        file_name = parent_directory + '/data/' +str(connection_type) + '_nx_graph.gexf'
        nx.write_gexf(friend_graph,file_name) 
        print("saved graph for ",connection_type)
    elif connection_type == 'higher_level_friend':
        higher_friend_graph = nx.Graph()
        connections = set()
        for s, p, o in rdf_graph:
            if str(p) =='http://www.w3.org/2006/vcard/ns#experiences':
                for trip in rdf_graph.triples((URIRef(o),None,None)):
                    if 'experience_details' in str(trip[1]):
                        role = get_person_role(trip[2])
                        subs = clean_sub(str(trip[2]))
                        if len(subs) >= 2 and role:
                            comp_uri = find_company_from_graph(subs[1])
                            if 'founder' in str(role).lower() or 'co founder' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['Founder']))
                                # print(s,role,comp_uri)
                            elif 'ceo' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['CEO']))
                                # print(s,role,comp_uri)
                            elif 'coo' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['COO']))
                                # print(s,role,comp_uri)
                            elif 'cio' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['CIO']))
                                # print(s,role,comp_uri)
                            elif 'president' in str(role).lower() or 'vice president' in str(role).lower() or 'vp' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['President']))
                                # print(s,role,comp_uri)
                            elif 'director' in str(role).lower() or 'md' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['Director']))
                                # print(s,role,comp_uri)
                            elif 'chief' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['Chief']))
                                # print(s,role,comp_uri)
                            elif 'manager' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['Manager']))
                            elif 'senior' in str(role).lower() or 'sr ' in str(role).lower():
                                connections.add((comp_uri,str(s),positions['Senior']))
                            else:
                                connections.add((comp_uri,str(s),10000000000))
                        else:
                            comp = get_company_from_one_uri(subs[0])
                            role = get_person_role(subs[0])
                            if comp and role:
                                if 'founder' in str(role).lower() or 'co founder' in str(role).lower():
                                    connections.add((comp,str(s),positions['Founder']))
                                    # print(s,role,comp_uri)
                                elif 'ceo' in str(role).lower():
                                    connections.add((comp,str(s),positions['CEO']))
                                    # print(s,role,comp_uri)
                                elif 'coo' in str(role).lower():
                                    connections.add((comp,str(s),positions['COO']))
                                    # print(s,role,comp_uri)
                                elif 'cio' in str(role).lower():
                                    connections.add((comp,str(s),positions['CIO']))
                                    # print(s,role,comp_uri)
                                elif 'president' in str(role).lower() or 'vice president' in str(role).lower() or 'vp' in str(role).lower():
                                    connections.add((comp,str(s),positions['President']))
                                    # print(s,role,comp_uri)
                                elif 'director' in str(role).lower() or 'md' in str(role).lower():
                                    connections.add((comp,str(s),positions['Director']))
                                    # print(s,role,comp_uri)
                                elif 'chief' in str(role).lower():
                                    connections.add((comp,str(s),positions['Chief']))
                                    # print(s,role,comp_uri)
                                elif 'manager' in str(role).lower():
                                    connections.add((comp,str(s),positions['Manager']))
                                elif 'senior' in str(role).lower() or 'sr ' in str(role).lower():
                                    connections.add((comp,str(s),positions['Senior']))
                                else:
                                    connections.add((comp,str(s),10000000000))
        higher_friend_graph.add_weighted_edges_from(connections)   
        print("Connections completed !!",len(higher_friend_graph.nodes())) 
        for node in higher_friend_graph.nodes():
            if "https://www.linkedin.com/in" in node or "http://example.org/candid/" in node:
                higher_friend_graph.nodes[node]['label'] = remove_non_printable_chars(find_label_from_uri(node))
            else:
                higher_friend_graph.nodes[node]['label'] = remove_non_printable_chars(find_label_from_uri(node))
                higher_friend_graph.nodes[node]['employees'] = '||'.join(find_all_people_in_company(node))
        file_name = parent_directory + '/data/' +str(connection_type) + '_nx_graph.gexf'
        nx.write_gexf(higher_friend_graph,file_name) 
        print("saved graph for ",connection_type,len(higher_friend_graph.nodes()))

# .________________________________________________________   ENDPOINTS FOR COMPANY TO PERSON PATH  _________________________________________________________________________________
# main calling function to find precedence path search
def shortestPath_for_HigherLevels(searching_person,target_company):
    nx_graph = load_nx_graph('higher_level_friend')
    source_uri = find_uri_from_nxlabel(searching_person,nx_graph)
    target_uri = find_uri_from_nxlabel(target_company,nx_graph)
    print(source_uri,target_uri)
    shortest_path_results = {}
    if source_uri != None and target_uri != None:
        all_employees_details = findall_current_nx_graph_employees(source_uri,nx_graph)
        persons_company = find_label_from_nx_graph(all_employees_details['company'],nx_graph)
        company_uri = all_employees_details['company']
        all_employees = all_employees_details['employees']
        shortest_path_results['data'] = []
        if all_employees:
            for employees in all_employees:
                    try:
                        shortest_paths = nx.all_shortest_paths(nx_graph,employees,target_uri,weight='weight')
                        if shortest_paths:
                            employe_results = {}
                            employe_results['name'] = find_label_from_nx_graph(employees,nx_graph)
                            employe_results['name_uri'] = employees 
                            employe_results['company'] = persons_company
                            employe_results['company_uri'] = company_uri
                            employe_results['shortest_paths'] = []
                            for all_paths in shortest_paths:
                                print('-'*50)
                                print(f"\nShortest Path From \t[{employees}]\t to \t[{target_company}] is :\n")
                                print(all_paths)
                                print("\n-----------------------------------------------------------------------------------")
                                employe_results['shortest_paths'].append(get_labelled_path(all_paths,nx_graph))
                            shortest_path_results['data'].append(employe_results)
                    except Exception as e:
                        print(e)
    else:
        print(f"Either {searching_person} or {target_company} not present in graph !! :(")
    print(shortest_path_results)
    return shortest_path_results


# main calling function to find nearest friend path search
def shortestPath_closestPerson(searching_person,target_company):
    nx_graph = load_nx_graph('nearest_friend')
    source_uri = find_uri_from_nxlabel(searching_person,nx_graph)
    target_uri = find_uri_from_nxlabel(target_company,nx_graph)
    print(source_uri,target_uri)
    shortest_path_results = {}
    if source_uri != None and target_uri != None:
        all_employees_details = findall_current_nx_graph_employees(source_uri,nx_graph)
        persons_company = find_label_from_nx_graph(all_employees_details['company'],nx_graph)
        company_uri = all_employees_details['company']
        all_employees = all_employees_details['employees']
        shortest_path_results['data'] = []
        if all_employees:
            for employees in all_employees:
                    try:
                        shortest_paths = nx.all_shortest_paths(nx_graph,employees,target_uri,weight='weight')
                        if shortest_paths:
                            employe_results = {}
                            employe_results['name'] = find_label_from_nx_graph(employees,nx_graph)
                            employe_results['name_uri'] = employees 
                            employe_results['company'] = persons_company
                            employe_results['company_uri'] = company_uri
                            employe_results['shortest_paths'] = []
                            for all_paths in shortest_paths:
                                print('-'*50)
                                print(f"\nShortest Path From \t[{employees}]\t to \t[{target_company}] is :\n")
                                print(all_paths)
                                print("\n-----------------------------------------------------------------------------------")
                                employe_results['shortest_paths'].append(get_labelled_path(all_paths,nx_graph))
                            shortest_path_results['data'].append(employe_results)
                    except Exception as e:
                        print(e)
    else:
        print(f"Either {searching_person} or {target_company} not present in graph !! :(")
    print(shortest_path_results)
    return shortest_path_results


# _____________________________________________ ENDPOINTS FOR PERSON TO PERSON PATH __________________________________________________

# main calling function to find person to person path search
def shortestPath_person_to_person(searching_person,target_person,filter_type):
    final_results = {}
    for filter in filter_type:
        nx_graph = load_nx_graph(filter)
        final_results[filter] = []
        source_uri = find_nxGraph_uri(searching_person,nx_graph)
        target_uri = find_nxGraph_uri(target_person,nx_graph)
        print(source_uri,target_uri)
        if source_uri != None and target_uri != None:
            try:
                shortest_paths = nx.all_shortest_paths(nx_graph,source_uri,target_uri)
                for all_paths in shortest_paths:
                    print('-'*50)
                    print(f"\nShortest Path From \t[{searching_person}]\t to \t[{target_person}] is :\n")
                    print(all_paths)
                    if filter == "connections":
                        label_dict = {}
                        for path in all_paths:
                            label_dict[path] = find_label_from_nx_graph(path,nx_graph)
                        final_results[filter].append(label_dict)
                    else:
                        final_results[filter].append(all_paths)
                    print("\n-----------------------------------------------------------------------------------")
            except Exception as e:
                print(e)
        else:
            print(f"Either {source_uri} or {target_uri} not present in graph !! :(")
    print(final_results)
    return final_results


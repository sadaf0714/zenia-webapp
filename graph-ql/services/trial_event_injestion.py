# results = arrange_fields_output(company_data.get('data'), "linkedin")
#                         new_company_data_set  = {}
#                         new_company_data_set['parent_name'] = profile['company']
#                         new_company_data_set['custom_properties']  =  results['custom_property']
#                         new_company_data_set['employer']  =  []#results['employer'] 
#                         new_company_data_set['social_url'] = results['social_url']
#                         new_company_data_set['name'] = profile['company']
#                         new_company_data_set['source'] = "linkedin"
#                         new_company_data_set['description'] =  clean_description(results["description"])
#                         new_company_data_set['headquarters'] =  results["headquarters"]
#                         new_company_data_set['no_of_employees'] =  results["no_of_employees"]
#                         new_company_data_set['company_type'] =  results["company_type"]
#                         new_company_data_set['specialities'] =  results["specialities"]
#                         new_company_data_set['industry'] =  results["industry"]
#                         new_company_data_set['social_url'] =   profile['company_linkedin_url']
                        
#                         if profile['is_current'] == True:
#                             if  results['industry'] == "" or results['industry'] == None:
#                                 new_company_data_set['industry'] = profile['company_industry']
                            
#                             if "founded" in results:
#                                 if  results['founded'] == "" or results['founded'] == None:
#                                     new_company_data_set['founded'] = profile['company_year_founded']
#                                 else:
#                                     new_company_data_set['founded'] = results['founded']
#                             else:
#                                 new_company_data_set['founded'] = profile['company_year_founded']
#                         else:
#                             if "founded" in results:
#                                 if  results['founded'] == "" or results['founded'] == None:
#                                     new_company_data_set['founded'] = ""
#                                 else:
#                                     new_company_data_set['founded'] = results['founded']
#                             else:
#                                 new_company_data_set['founded'] = ""

#                         new_company_data_set['manual'] = "Yes"
                        
#                         utctimenow = datetime.now(timezone.utc)
#                         new_company_data_set['timestamp'] = utctimenow.strftime('%d-%m-%YT%T')
                        
#                         #reset empployer object
#                         new_company_data_set['employer'].append({
#                             'occupation': profile['job_title'],
#                             'social_url': profile['linkedin_url'],
#                             'description': description,
#                             'source': 'linkedin',
#                             'first_name': profile['first_name'],
#                             'last_name': profile['last_name'],
#                             "start_month":profile['start_month'],
#                             "start_year":profile['start_year'],
#                             "end_month":profile['end_month'],
#                             "end_year":profile['end_year'],
#                             "duration":profile['duration'],
#                             "date_range":profile['date_range'],
#                             "employee_role_description":profile['job_role_description'],
#                             "is_current": profile['is_current'],
#                             "skills":profile['skills'],
#                             "languages":profile['languages'],
#                             "location":profile['location']
#                         })

#                         for item in new_company_data_set['employer']:
#                             item['full_name'] = item['first_name'] + ' ' + item['last_name']
#                             if item["occupation"] == None :
#                                 item["occupation"] = "" 
#                             #del item['first_name']
#                             #del item['last_name']
                        
#                         #store data in graph and redis through choreo endpoint
#                         print(f'choreo process start ID : {i}')
#                         time.sleep(5)
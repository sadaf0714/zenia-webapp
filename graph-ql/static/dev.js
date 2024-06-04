var GRAPH_DB_URL;
var REDIS_SERVICE_URL;
var GRAPHQL_SERVICE;
var DEFAULT_REPO;
var redisServiceGetSuggestion;
var redisServiceGetSuggestionCrawl;
var graphVisualUrl;
var graphQLEndpoint;
var graphDB_Login;
var graphDB_Repo;
var VECTOR_SERVICE; 
var standards_fields;
var standards_fields_linkedin;
var standards_fields_dbpedia;
var graph_db_visual_url;
var metaphactory_url;
var showKgToggle  = "onto";
let hostname = window.location.host
 
var graphql_host = window.location.protocol+'//'+hostname+'/graphql';
var graphql_host_domain = window.location.protocol+'//'+hostname
 
/*var graphql_host; 
if(hostname=="localhost" || hostname=="127.0.0.1"){
    graphql_host = 'http://127.0.0.1:8000/graphql';
}
else if(hostname=="api.zeniagraph.ai"){
  graphql_host = 'https://api.zeniagraph.ai/graphql';
}
else{
    graphql_host = 'http://44.202.144.84:8000/graphql';
}*/

var settings = {
  async: false,
  "url": graphql_host,
    "method": "POST",
    "timeout": 0,
    "headers": {
      "Content-Type": "application/json"
    },
    "data": JSON.stringify({
      query: "query getEnvVariables{\r\n        getEnvVariables{\r\n    graph_db_visual_url\r\n  metaphactory_url\r\n       default_repo\r\n            graph_db_url\r\n            redis_service\r\n            graphql_service\r\n      vector_service\r\n  standards_fields\r\n standards_fields_linkedin\r\n  standards_fields_dbpedia }\r\n}",
      variables: {}
    })
  };
  
  function getVariables(settings){ 
    $.ajax(settings).done(function (response) {
        if(response.data.getEnvVariables[0]){
              
              keys = response.data.getEnvVariables[0]
                 
              GRAPH_DB_URL = keys.graph_db_url;
              REDIS_SERVICE_URL = keys.redis_service;
              DEFAULT_REPO = keys.default_repo;
              VECTOR_SERVICE = keys.vector_service
              graph_db_visual_url = keys.graph_db_visual_url
              metaphactory_url = keys.metaphactory_url

              redisServiceGetSuggestion = REDIS_SERVICE_URL + '/redis/api/get-name-suggestion'
              redisServiceGetSuggestionCrawl = REDIS_SERVICE_URL + '/redis/api/get-crawl-name-suggestion'
              graphVisualUrl = graph_db_visual_url + '/graphs-visualizations?query='
              graphQLEndpoint =  graphql_host

              graphDB_Login = GRAPH_DB_URL + '/rest/login';
              graphDB_Repo = GRAPH_DB_URL + '/repositories';

              standards_fields = keys.standards_fields
              standards_fields_dbpedia = keys.standards_fields_dbpedia
              standards_fields_linkedin = keys.standards_fields_dbpedia
        }
    });
}

getVariables(settings)


$( document ).ready(function() {
  
  $('.global_toggle_uid span').click(function(){  
      let tabvalue = $(this).data('tab')
      $('.global_toggle_uid span').removeClass('active')
      $(this).addClass('active')
      if(tabvalue=="meta"){
        showKgToggle = "meta"
      }else{
        showKgToggle = "onto"
      }
      replaceShowKGUrls(showKgToggle)
  })
})

function capitalizeFLetter(string) {
  return string[0].toUpperCase() + string.slice(1);
}
 
function encodeURIVisual(string){
  return string.replaceAll("(", "%28").replaceAll(")", "%29");
}

function replaceShowKGUrls(showKgToggle){
   
  //Update all 'showkg' URLs in the DOM based on the current toggle value.
  $("a").each(function(index, item) {
    let url = $(item).attr("href");
    var finalString  = ""
    if(url!="" && typeof url!== "undefined"){
        if(url.includes(graph_db_visual_url) || url.includes(metaphactory_url)){
            if(showKgToggle=="meta"){
                if(url.includes(graph_db_visual_url)){
                    finalString = url.replace(`${graph_db_visual_url}/graphs-visualizations?uri=`,`${metaphactory_url}/resource/?uri=`)
                    $(item).attr("href", finalString);
                }
            }else if(showKgToggle=="onto"){
                if(url.includes(metaphactory_url)){
                    finalString = url.replace(`${metaphactory_url}/resource/?uri=`, `${graph_db_visual_url}/graphs-visualizations?uri=`)
                    $(item).attr("href", finalString);
                }
            }                    
        }
    }
  })
}

function visualGraphShowKG(url, type){
             
  var finalString  = ""
  var metaphactResourceURI = ""
  
  if(type=="full"){
      metaphactResourceURI = `resource/:showKG?query=`
  }else if(type=="single"){
      metaphactResourceURI = `resource/?uri=`
  }

  if(showKgToggle == "meta"){
      if(url.includes(graph_db_visual_url)){

          if(url.includes('graphs-visualizations?query=')){
              url = url.replace("graphs-visualizations?query=","graphs-visualizations?uri=")
          }

          finalString = url.replace(`${graph_db_visual_url}/graphs-visualizations?uri=`,`${metaphactory_url}/${metaphactResourceURI}`)
      }else{
          finalString = url
      }
  }else if(showKgToggle == "onto"){
      if(url.includes(metaphactory_url)){
          finalString = url.replace(`${metaphactory_url}/${metaphactResourceURI}`, `${graph_db_visual_url}/graphs-visualizations?uri=`)
      }else{
          finalString = url
      }
  }
  return finalString
}

function getDomainName(url) {
  // Remove protocol
  let domain = url.replace(/^.*?:\/\//, '');

  // Remove www
  domain = domain.replace(/^www\./, '');

  // Remove path
  domain = domain.replace(/\/.*$/, '');

  // Split by dots and get the first part
  const parts = domain.split('.');
  if (parts.length >= 2) {
      domain = parts[parts.length - 2];
  }

  // Capitalize the first letter
  domain = domain.charAt(0).toUpperCase() + domain.slice(1);

  return domain;
}
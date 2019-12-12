# Import libraries
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic

import rdflib
from rdflib import Graph
from rdflib.util import guess_format



import pandas as pd
import os
import math
import requests

import ckan.plugins.toolkit as toolkit

import ckan.lib.helpers as helpers

import csv
from itertools import izip_longest



# Import the package for the update function from the logic folder
import ckanext.liveschema_theme.logic.updater
import ckanext.liveschema_theme.logic.fca_generator
import ckanext.liveschema_theme.logic.cue_generator
import ckanext.liveschema_theme.logic.visualization_generator

# Get the function from toolkit
enqueue_job = toolkit.enqueue_job
# Get the function from logic
get_action = logic.get_action

# Define the action of updater of LiveSchema
def updater(context, data_dict):
    # Enqueue the script to be executed by the background worker
    enqueue_job(ckanext.liveschema_theme.logic.updater.updateLiveSchema, args=[data_dict], title="updateLiveSchema", queue=u'default', timeout=-1)

# Define the action of fca_generator of LiveSchema
def fca_generator(context, data_dict):
    # Enqueue the script to be executed by the background worker
    #resource_patch
    enqueue_job(ckanext.liveschema_theme.logic.fca_generator.generateFCA, args=[data_dict], title="generateFCA", queue=u'default', timeout=-1)

# Define the action of cue_generator of LiveSchema
def cue_generator(context, data_dict):
    # Enqueue the script to be executed by the background worker
    enqueue_job(ckanext.liveschema_theme.logic.cue_generator.generateCue, args=[data_dict], title="generateCue", queue=u'default', timeout=-1)

# Define the action of visualization_generator of LiveSchema
def visualization_generator(context, data_dict):
    # Enqueue the script to be executed by the background worker
    enqueue_job(ckanext.liveschema_theme.logic.visualization_generator.generateVisualization, args=[data_dict], title="generateVisualization", queue=u'default', timeout=-1)

# Define the action of reset resources of LiveSchema
def reset(context, data_dict):
    # Enqueue the script to be executed by the background worker
    enqueue_job(ckanext.liveschema_theme.logic.updater.addResources, args=[data_dict['id'], data_dict['package']], title="resetResources", queue=u'default', timeout=-1)


# Define the action of query of LiveSchema
def query(context, data_dict):
    # Get the resource and query from the form
    N3Resource = data_dict["N3Resource"]
    query = data_dict["query"]
    try:
        # Try to create the graph to analyze the vocabulary
        g = Graph()
        result = g.parse(N3Resource["url"], format=guess_format("n3"), publicID=N3Resource["name"])
        # Query the dataset
        qres = g.query(query)

        # Save the result of the query
        result = list()
        for row in qres:
            rowRes = list()
            for res in row:
                if(res):
                    rowRes.append(res.toPython())
            result.append(rowRes)
        # Return the result of the query
        return result
    except Exception as e:  
        # Return the exception
        return [["Exception: " +str(e)]]


# Define the action of KLotus of LiveSchema
def visualization_lotus(context, data_dict):
    # Create the dataframe from the FCA file
    data = pd.read_csv(data_dict["FCAResource"])

    # Create the DataFrame used to save the occurrences of the Types present on the Token row
    DF = pd.DataFrame(columns=["Token", "Types"])

    # Create the set used to check if new Types has to be added or if existing Types has to be updated
    tokens = set()
    # Iterate over every row of the matrix
    for index, row in data.iterrows():
        # Iterate over overy tokenized column of the matrix
        for column in data.columns[2:]:
            # If the row has a value, then add the token to the list of the TypeTerm
            if(row[column]):
                # Check if new column has to be added or if existing column has to be updated
                a = len(tokens)
                tokens.add(str(column))
                if(a < len(tokens)):
                    DF.at[str(column), "Token"] = column
                    DF.at[str(column), "Types"] = str(row["TypeTerm"])
                else:
                    types = str(DF.at[str(column), "Types"])
                    DF.at[str(column), "Types"] = types + " , " + str(row["TypeTerm"])

    # Create the DataFrame used to save the table used to identify common Tokens between Types
    DTF = pd.DataFrame(columns=["total", "Types", "number", "Tokens"])
    # Create the set used to check if new Types has to be added or if existing Types has to be updated
    set_ = set()
    # Iterate for every row present on DF, for every Token and the relative Types
    for index_, row in DF.iterrows():
        # Check if new Types has to be added or if existing Types has to be updated
        a = len(set_)
        set_.add(str(row["Types"]))
        if(a < len(set_)):
            # Create a new row on the DataFrame for that Types
            DTF.at[str(row["Types"]), "total"] = len(str(row["Types"]).split(","))
            DTF.at[str(row["Types"]), "Types"] = row["Types"]
            DTF.at[str(row["Types"]), "Tokens"] = str(row["Token"])
            DTF.at[str(row["Types"]), "number"] = 1
        else:
            # Update the row for that Types, adding the new Token
            elements = str(DTF.at[str(row["Types"]), "Tokens"])
            number = DTF.at[str(row["Types"]), "number"]
            DTF.at[str(row["Types"]), "Tokens"] = elements + " , " + str(row["Token"])
            DTF.at[str(row["Types"]), "number"] = number + 1

    DTF = DTF.sort_values(by='total', ascending=False)

    DTF = DTF.sort_values(by='number', ascending=False)

    colSel = list()
    thres = 0
    for index_, row in DTF.iterrows():
        if(4 <= row["total"] <= 6 ):
            if(row["total"]*row["number"] > thres): # [TODO] To think about a more complex selection
                thres = row["total"]*row["number"]
                colSel = list()
                for a in  row["Types"].split(","):
                    colSel.append(a.strip())

    ##loading data
    data = pd.read_csv(data_dict["visualizationResource"], dtype='unicode')

    #Make a direction to the temporary file(which is created for generating plots)
    dir_ = "src/ckanext-liveschema_theme/ckanext/liveschema_theme/public/"
    
    for column in data:
        if( column.strip() not in colSel):
            data.drop(column, axis=1, inplace=True)

    file_name = sep_file(dir_ + "resources/",data)
    plot_Venn(dir_, file_name)

    del_file(dir_ + "resources/",data)

#Separate a csv file into target input files
def sep_file(dir_, data):
    file_name =[]
    for column in data:
        file_content = data[column].dropna(axis=0,how='all')
        file_n = dir_ + column+".csv"
        file_content.to_csv(os.path.normpath(os.path.expanduser(file_n)))
        file_name.append(file_n)
    return file_name

#Delete the temporary inputs
def del_file(dir_,data):
    for column in data:
        file_n = dir_ + column + ".csv"
        if (os.path.exists(file_n)):
            os.remove(file_n)

#The Venn plot function
def plot_Venn(dir_, file_name):
    if 2<=len(file_name)<=6:
        a = os.system(r"intervene venn -i "+str(dir_ + "resources/")+"*.csv --output "+str(dir_ + "KLotus/")+" --type list --figtype png")

#The UpSet plot function
def plot_UpSet(file_name):
    if 2 <= len(file_name) <= 6:
        a = os.system(r"intervene upset -i data1/*.csv --output Results --type list --figtype png")

#The Pairwise plot function
def plot_Pairwise(file_name):
    if 2 <= len(file_name) <= 20:
        os.system(r"intervene pairwise -i data1/*.csv --output Results --type list --figtype png")



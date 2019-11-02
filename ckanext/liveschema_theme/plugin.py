# encoding: utf-8
# Import libraries
import ckan.plugins as plugins

import ckan.plugins.toolkit as toolkit

from ckan.plugins import IRoutes, implements, SingletonPlugin
from ckan.lib.base import BaseController
from ckan.config.routing import SubMapper

# Import the package for the update function from the logic folder
from ckanext.liveschema_theme.logic.updater import updateLiveSchema

# Get the biggest catalogs ordered by the number of contained datasets
def most_popular_catalogs():
    '''Return a sorted list of the catalogs with the most datasets.'''

    # Get a list of all the site's catalogs from CKAN, sorted by number of
    # datasets.
    catalogs = toolkit.get_action('organization_list')(
        data_dict={'sort': 'package_count desc', 'all_fields': True})

    # Truncate the list to the 10 most popular catalogs only.
    catalogs = catalogs[:10]

    # Return the list of catalogs
    return catalogs

# Get the list of datasets that have the relative csv file
def dataset_selection():
    '''Return a list of the datasets with their relative resources.'''

    # Get a list of all the datasets.
    datasets = toolkit.get_action('package_list')(
        data_dict={})

    # Create the list of datasets that have the relative csv file to return
    dataSetSelection = list()

    # Iterate over every datasets
    for data in datasets:
        # Get the information about every dataset
        dataSet = toolkit.get_action('package_show')(
            data_dict={"id": data})
        # Iterate over every resource of the dataset
        for res in dataSet["resources"]:
            # Check if they have the relative csv file
            if(res["format"]=="CSV"):
                # Append the dataset with the basic information about it
                dataSetSelection.append({"name": data, "link": res["url"], "title": dataSet["title"]})

    # Return the list of datasets that have the relative csv file to return
    return dataSetSelection


class LiveSchemaThemePlugin(plugins.SingletonPlugin):
    '''LiveSchemaThemePlugin'''
    # Declare that this class implements IConfigurer.
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config):

        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        # 'templates' is the path to the templates dir, relative to this
        # plugin.py file.
        toolkit.add_template_directory(config, 'templates')

        # Add this plugin's public dir to CKAN's extra_public_paths, so
        # that CKAN will use this plugin's custom static files.
        toolkit.add_public_directory(config, 'public')

    # Declare that this plugin will implement ITemplateHelpers.
    plugins.implements(plugins.ITemplateHelpers)

    def get_helpers(self):
        '''Register the most_popular_catalogs() function above as a template
        helper function.'''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {'liveschema_theme_most_popular_catalogs': most_popular_catalogs, 'liveschema_theme_dataset_selection': dataset_selection}   

    # Edit the Routes of CKAN to add custom ones for the services
    implements(IRoutes, inherit=True)

    def before_map(self, map):

        # These named routes are used for custom dataset forms which will use
        # the names below based on the dataset.type ('dataset' is the default type)

        # Define the custom Controller for the routes of ckanext_LiveSchema_theme
        LiveSchemaController = 'ckanext.liveschema_theme.plugin:LiveSchemaController'

        # Define the list of new routes to be added
        map.connect('ckanext_liveschema_theme_services', '/service', controller=LiveSchemaController, action='index')
        map.connect('ckanext_liveschema_theme_fca_generator', '/service/fca_generator', controller=LiveSchemaController, action='fca_generator')
        map.connect('ckanext_liveschema_theme_cue_generator', '/service/cue_generator', controller=LiveSchemaController, action='cue_generator')
        map.connect('ckanext_liveschema_theme_updater', '/service/updater', controller=LiveSchemaController, action='updater')
        map.connect('ckanext_liveschema_theme_update', '/service/update', controller=LiveSchemaController, action='update')
        
        # Return the new configuration to the default handler of the routers
        return map

# Base Controller to handle the new routes for the services of LiveSchema
class LiveSchemaController(BaseController):

    # Define the behaviour of the index of services
    def index(self):
        return toolkit.render('service/services.html')

    # Define the behaviour of the fca generator
    def fca_generator(self):
        # If the page has to handle the form resulting from the service
        if toolkit.request.method == 'POST' and toolkit.request.params['dataset']:
            # Get the selected dataset
            dataset = toolkit.request.params['dataset']
            # Go to the dataset page
            return toolkit.redirect_to(controller='package', action='read',
                    id=dataset)
        # Render the page of the service
        return toolkit.render('service/fca_generator.html')
    

    # Define the behaviour of the cue generator
    def cue_generator(self):
        # If the page has to handle the form resulting from the service
        if toolkit.request.method == 'POST' and toolkit.request.params['dataset']:
            # Get the selected dataset
            dataset = toolkit.request.params['dataset']
            # Go to the dataset page
            return toolkit.redirect_to(controller='package', action='read',
                    id=dataset)
        # Render the page of the service
        return toolkit.render('service/cue_generator.html')

    # Define the behaviour of the updater service
    def updater(self):
        # Render the page of the service
        return toolkit.render('service/updater.html')

    # Define the behaviour of the update function
    def update(self):
        # Enqueue the script to be executed by the background worker
        toolkit.enqueue_job(updateLiveSchema, title="LiveSchemaUpdater", queue=u'default')
        #updateLiveSchema()
        # Redirect to the index
        return toolkit.redirect_to("../")
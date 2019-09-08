# -*- coding: utf-8 -*-
import pandas as pd

from AlationInstance import AlationInstance
from Article import Article
from alationutil import log_me
from secure_copy import secure_copy
from query import *

# import the necessary packages
import argparse
import re
import time
import json

if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--username",  required=True,  help="username")
    ap.add_argument("-p", "--password",  required=True,  help="password")
    ap.add_argument("-H", "--host",      required=True,  help="URL of the Alation instance")
    ap.add_argument("-v", "--username2", required=False, help="username2")
    ap.add_argument("-w", "--password2", required=False, help="password2")
    ap.add_argument("-x", "--host2",     required=False, help="URL of the 2nd Alation instance")
    args = vars(ap.parse_args())

    url_1    = args['host']
    user_1   = args['username']
    passwd_1 = args['password']
    alation_1 = AlationInstance(url_1, user_1, passwd_1)
    user_1_only = user_1.split(u'@')[0]

    desired_template = u"ABOK Article"
    log_me(u"Getting desired articles")
    allArticles  = alation_1.getArticles(template=desired_template) # download all articles
    Art = Article(allArticles)                    # convert to Article class
    queries = alation_1.getQueries(ds_id=1)
    # queries.to_csv("AA Queries.csv", encoding='utf-8', index=False)

    # queries_from_csv = pd.read_csv("AA Queries.csv")

    query_html = generate_html(queries)

    url_2    = args['host2']
    user_2   = args['username2']
    passwd_2 = args['password2']
    alation_2 = AlationInstance(url_2, user_2, passwd_2)

    m = Art.convert_references_2()
    #alation_2.putQueries(ds_id=5, queries=queries)

    # log_me(u"Getting media files links")
    # media = Art.get_files()
    # dir = u'/Users/' + user_1_only + u'/Downloads'
    # log_me(u"Getting media files via download, dir={}".format(dir))
    # alation_1.getMediaFile(media, dir)

    log_me(u"Creating PDF")
    Art.create_pdf(first=51, additional_html=query_html)

    # log_me(u"Securely copying media files to remote host")
    # secure_copy(host='3.130.86.60',
    #             username='ec2-user',
    #             key_filename='/Users/matthias.funke/.ssh/LightsailDefaultKey-us-east-2.pem',
    #             local_dir=dir+u"/media/image_bank")



    #log_me(u"Creating CSV")
    #Art.to_csv(desired_template + ".csv")
    allTemplates = alation_1.getTemplates()          # download all templates (with their custom fields)
    # We need to have quite detailed information to create the template!

    custom_fields = alation_1.getCustomFields_from_template(desired_template) # this way we also get the template info

    # create a migration notes field to hold manual migration instructions
    #migration_error = dict(allow_multiple=False, allowed_otypes=None, backref_name=None, backref_tooltip_text=None,
    #                       builtin_name=None, field_type=u'RICH_TEXT',
    #                       name_plural=u'Migration Notes', name_singular=u'Migration Notes',
    #                       options=[])

    #if custom_fields.shape[0]>0:
    #    custom_fields = custom_fields.append(migration_error, ignore_index=True)


    # Next, we put the objects we want. We need to start with the custom fields, then the template,
    # then the articles, and finally the glossaries.

    target = AlationInstance(args['host2'], args['username2'], args['password2'])
    c_fields = target.putCustomFields(custom_fields) # returns a list of field IDs (existing or new)
    desired_template_pd = allTemplates[allTemplates.title==desired_template]
    t = target.putCustomTemplate(desired_template_pd, c_fields) # returns the ID of the (new) template
    #target.putGlossaries(glossaries) --- NOT IMPLEMENTABLE YET DUE TO LACK OF API
    result = target.putArticles(Art, desired_template, c_fields)
    log_me(result.content)

    target.fix_refs()
    target.fix_children(allArticles)






README.txt

deploy_vars is equivalent to group_vars except that 
while group_vars matches an inventory hosts file 
( or hostvars[groups] from dynamic inventory)
with folders that are direct children of group_vars/ and all
desendent folders of matches are loaded; deploy_vars
uses the deploy_vars.py plugin which I wrote in vars_plugins/ and 
checks at each sub-folder that the folder-name matches 
a hostvars[groups] and only descends on a match.

blue/green deploy groups are used if you have some infrastructure 
that requires heavy lifting, for example an RDBMS that
can backend either production or staging.  This allows
a "firmware" layer for networks and heavy resources while
prod/staging deployments can switch back and forth over
blue/green firmware.

Sample inventory hosts files:

Since aws cloud management commnads are run against localhost
the inventory file simply maps to the config files needed in deploy_vars.
> cat prod_green_hosts
####### DEPLOY SPECIFIC GROUPS ######
[deploy_vars:children]
aws
[aws:children]
green
prod
[prod]
localhost
########## ROLE GROUPS #########
[vpc]
localhost
[route53]
localhost
...

Note that this inventory file is to maintain or create a prod/green deployment.  A separate, more complex playbook would be required
to acturally perfom the migration from (prod/green, stage/blue) to 
(prod/blue, stage/green) 

Dynamic inventory would be used to manage the actual vms created 
within the aws cloud.

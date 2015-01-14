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
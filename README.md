Code to do data analysis and visualization for PBR/Project Pavement.

Here's the link to the data folder containing csvs: https://www.dropbox.com/sh/ra7sugy3fuljd9k/AAAjBBRN5mcD3YVxtVmaW8X8a?dl=0 (if you don't have admin access to dump the data yourself)

Trello is here: https://trello.com/b/2VqLq7US/project-pavement

Currently, the URLs for the project are

https://github.com/strangerloops/pavement_android

https://github.com/strangerloops/pavement_ios

https://github.com/strangerloops/pavement_rails

http://project-pavement.herokuapp.com/

https://github.com/ifed3/PBR

Join ChiHackNight Slack here: http://chihacknightslack.herokuapp.com/
And we're the #pbr subchannel.
URL should look something like this? https://chihacknight.slack.com/messages/pbr/

You can use conda to install most of the dependencies, but this project
also uses rtree which is not installable from conda. I think Shapely and PyProj are just wrappers for other libraries that you'll have to somehow install.

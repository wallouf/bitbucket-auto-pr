# bitbucket-auto-pr
Search throught Bitbucket projects / repo / branch and create PR for all repo that have more than x diff

# parameters

This python require 7 parameters:
 - team name ( string )
 - username ( string )
 - password ( string )
 - project name beginning with to search ( string )
 - source branch ( string )
 - destination branch ( string )
 - diff number min to trigger PR creation ( int )
 
 ## Note: 
  - Parameters can be given at call, or by input
 ### example:
  - py auto-pr.py team user pwd project source destination 3
  - py auto-pr.py
    
 
 # behavior
 
 This python will:
  - scan all the projects starting with the prefix ( if defined )
  - exclude project with names according to parameters
  - search all repositories linked to these projects
  - get diff between source branch and destination branch
  - if diff is higher or egal than diff trigger set, create a Pull-Request
  - print and write the Pull-Request link in a file and console

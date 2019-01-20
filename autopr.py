# Version: 0.0.4-SNAPSHOT
import json, requests, base64, sys

#generic var
URL_project = 'https://api.bitbucket.org/2.0/teams/'
URL_project_suffix = '/projects/'

URL_repositories = 'https://api.bitbucket.org/2.0/repositories/'
URL_suffix_query_repositories = '?q=project.key%3D%22'
URL_suffix_branches = '/refs/branches'
URL_suffix_diffstat = '/diffstat/'
URL_suffix_pullrequest = '/pullrequests/'



def main():
        repositories = []
        repositories_to_pr = []

        if len(sys.argv) >= 8:
                #Retrieve team name
                teamname = sys.argv[1]
                #Retrieve basic credentials for api calls
                username = sys.argv[2]
                password = sys.argv[3]
                #prefix to scan projects
                project_begin_with = sys.argv[4]
                #source and destination branches
                source = sys.argv[5]
                destination = sys.argv[6]
                #trigger for PR
                change_min_counter_trigger_for_PR = int(sys.argv[7])
        else:
                #Retrieve team name
                teamname = input("Enter Bitbucket team name: ")

                #Retrieve basic credentials for api calls
                username = input("Enter Bitbucket username: ")
                password = input("Enter Bitbucket password: ")
                #prefix to scan projects
                project_begin_with = input("Enter Bitbucket project prefix to scan: ")
                #source and destination branches
                source = input("Enter Bitbucket source branch: ")
                destination = input("Enter Bitbucket destination branch: ")
                #trigger for PR
                change_min_counter_trigger_for_PR = input("Enter diff min number to trigger PR: ")

        pwd = username + ':' + password
        base64_pwd = 'Basic ' + base64.b64encode(pwd.encode('utf-8')).decode('utf-8')

        print('### GET ALL PROJECTS FOR EPS')
        # GET ALL PROJECTS FOR EPS
        projects = list_projects(base64_pwd, teamname, project_begin_with)
        print('\tFound: ' + str(len(projects)) + ' active projects')

        # GET ALL REPO FOR THESE PROJECTS
        print('### GET ALL REPO FOR THESE PROJECTS')
        for project in projects:
                repositories = repositories + list_repo(project, base64_pwd, teamname)
        print('\tFound: ' + str(len(repositories)) + ' repositories')

        # GET DIFF BETWEEN LAST COMMIT FOR EACH REPO
        print('### GET DIFF BETWEEN BRANCHES LAST COMMIT FOR EACH REPO')
        for repository in repositories:
                if compare_branches_and_check_required_PR(repository, base64_pwd, teamname,source, destination, change_min_counter_trigger_for_PR):
                        repositories_to_pr.append(repository)
        print('\tFound: ' + str(len(repositories_to_pr)) + ' repositories that required a PR')

        # CREATE PR FOR REPO THAT REQUIRED ONE
        print('### CREATE PR FOR REPO THAT REQUIRED ONE')
        if len(repositories_to_pr) > 0:
                f = open("pullrequests_links.txt","w+")
                f.write("\n")
                pr_object = create_PR_object(source, destination)
                for repository in repositories_to_pr:
                        pr_object['source']['repository']['full_name'] = 'expertustechnologies/' + str(repository)
                        url_pr = str(create_PR(repository, pr_object, base64_pwd, teamname))
                        if url_pr != 'None':
                                f.write(url_pr + "\n")
                f.write("\n")
        print('### END OF SCRIPT. You can find PR links in the file "pullrequests_links.txt"')
def create_PR_object(source, destination):
        pr_object = {}
        pr_object['title'] = 'Merge branches'
        pr_object['description'] = 'Automatic'
        pr_object['close_source_branch'] = False
        pr_object['reviewers'] = []
        pr_object['destination'] = {}
        pr_object['destination']['branch'] = {}
        pr_object['destination']['branch']['name'] = destination
        pr_object['source'] = {}
        pr_object['source']['branch'] = {}
        pr_object['source']['branch']['name'] = source
        pr_object['source']['repository'] = {}
        return pr_object

def create_PR(repository, pr_object, base64_pwd, teamname):
        try:
                header={
                'Authorization': base64_pwd,
                'Content-Type': 'application/json'

                }
                url = URL_repositories + teamname + '/' + repository + URL_suffix_pullrequest
                resp = requests.post(url, headers=header, data=json.dumps(pr_object))
                if resp.status_code != 201:
                        print('Cannot create PR : response code: ' + str(resp.status_code) + 'reason: '+ str(resp.reason))
                        return 
                repo = json.loads(resp.text)
                url_pr = repo['links']['self']['href']
                print("\t\t" + str(url_pr))
                return url_pr
        except Exception as e:
                print(e)
                return



def compare_branches_and_check_required_PR(repository, base64_pwd, teamname, source, destination, change_min_counter_trigger_for_PR):
        destination_commit_id = None
        source_commit_id = None
        result = False
        try:
                header={
                'Authorization': base64_pwd
                }
                url = URL_repositories + teamname + '/' + repository.lower() + URL_suffix_branches
                while url:
                        resp = requests.get(url, headers=header)
                        if resp.status_code != 200:
                                print('Cannot get branches: response code: ' + str(resp.status_code))
                                return result
                        repo = json.loads(resp.text)
                        for repo in repo['values']:
                                if repo['name'] == destination:
                                        destination_commit_id = repo['target']['hash']
                                if repo['name'] == source:
                                        source_commit_id = repo['target']['hash']
                        if (source_commit_id and destination_commit_id) or 'next' not in repo:
                                break
                        url = repo['next']
                if source_commit_id and destination_commit_id:
                        total_changes = 0
                        url = URL_repositories + teamname + '/' + repository.lower() + URL_suffix_diffstat + source_commit_id + '..' + destination_commit_id
                        resp = requests.get(url, headers=header)
                        if resp.status_code != 200:
                                print('Cannot get diff: response code: ' + str(resp.status_code))
                                return result
                        repo = json.loads(resp.text)
                        for repo in repo['values']:
                                total_changes += repo['lines_removed']
                                total_changes += repo['lines_added']
                        if total_changes >=      change_min_counter_trigger_for_PR:
                                print("\t\t[ PR ] Diff between branches for " + str(repository) + ": " + str(total_changes))
                                return True
                        else:
                                print("\t\tDiff between branches for " + str(repository) + ": " + str(total_changes))
                return result
        except Exception as e:
                print(e)
                return result


# Get organizations to check input from calls
def list_repo(project, base64_pwd, teamname):
        return_repo = []
        try:
                header={
                'Authorization': base64_pwd
                }
                url = URL_repositories + teamname + URL_suffix_query_repositories + project + '%22'
                while url:
                        resp = requests.get(url, headers=header)
                        if resp.status_code != 200:
                                print('Cannot get repo: response code: ' + str(resp.status_code))
                                return return_repo
                        repo = json.loads(resp.text)
                        for repo in repo['values']:
                                return_repo.append(repo['name'])
                        if 'next' not in repo:
                                break
                        url = repo['next']
                return return_repo
        except Exception as e:
                print(e)
                return return_repo

# Get organizations to check input from calls
def list_projects(base64_pwd, teamname, project_begin_with):
        return_projects = []
        try:
                header={
                'Authorization': base64_pwd
                }
                url = URL_project + teamname + URL_project_suffix
                while url:
                        resp = requests.get(url, headers=header)
                        if resp.status_code != 200:
                                print('Cannot get projects: response code: ' + str(resp.status_code))
                                return return_projects
                        projects = json.loads(resp.text)
                        for project in projects['values']:
                                if project['key'].startswith(project_begin_with):
                                        return_projects.append(project['key'])
                        if 'next' not in projects:
                                break
                        url = projects['next']
                return return_projects
        except Exception as e:
                print(e)
                return return_projects


if __name__ == '__main__':
    main()
class Workflow:
    """
    Creates or loads a workflow. It also contains methods to manipulate the workflow.

    Workflow is a sequence of tasks. Each task can be either independent or dependent on other tasks,
    for instance it processes the output of other tasks.

    Construction::
    w1 = Workflow(name="sample", author="sample author", abstract="Sample abstract", url=None, sessionid=None, ncores=2,
                    nhost=2, on_error=None, on_exist=None, run=None, cwd=None, cdd=None, cube=None, callback_url=None,
                    output_format=None, host_partition=None, nthreads=None)


    Parameters
    ----------
    name: str
        workflow name
    author: str
        workflow author
    abstract: str
        workflow description
    url: str, optional
        workflow URL
    sessionid: str, optional
        session id for the entire workflow
    exec_mode: str, optional
        execution mode of the workflow, sync or async
    ncores: int, optional
        number of cores
    nhost: int, optional
        number of hosts
    on_error: str, optional
        behaviour in case of error
    on_exit: str, optional
        operation to be executed on output objects
    run: str, optional
        enable submission to analytics framework, yes or no
    cwd: str, optional
        current working directory
    cdd: str, optional
        absolute path corresponding to the current directory on data repository
    cube: str, optional
        cube PID for the entire workflow
    callback_url: str, optional
        callback URL for the entire workflow
    output_format: str, optional
        mode to code workflow output
    host_partition: str, optional
        name of host partition to be used in the workflow
    nthreads: str, optional
        number of threads

    """
    attributes = ["url", "sessionid", "exec_mode", "ncores", "nhost", "on_error", "on_exit", "run", "cwd", "cdd",
                  "cube", "callback_url", "output_format", "host_partition", "nthreads"]
    active_attributes = ["name", "author", "abstract"]
    task_attributes = ["run", "on_exit", "on_error"]
    task_name_counter = 1
    subworkflow_names = []

    def __init__(self, name, author=None, abstract=None, **kwargs):
        for k in kwargs.keys():
            if k not in self.attributes:
                raise AttributeError("Unknown workflow argument: {0}".format(k))
            self.active_attributes.append(k)
        self.name = name
        self.author = author
        self.abstract = abstract
        self.tasks = []
        self.__dict__.update(kwargs)

    def deinit(self):
        """
        Reverse the initialization of the object
        """
        for k in self.active_attributes:
            self.__delattr__(k)

    def addTask(self, task):
        """
        Adds tasks to workflow

        Parameters
        ----------
        task : <class 'pav.Task'>
            Task to be added to the workflow

        Raises
        ------
        AttributeError
            If the task name is already in the Workflow or if a dependency is not fulfilled

        Example
        -------
        t1 = Task(name="Import Type Selection Historical", operator="oph_if", arguments=None)
        w1.addTask(t5)
        """
        if "name" not in task.__dict__.keys() or task.name is None:
            task.name = self.name + "_{0}".format(self.task_name_counter)
        if task.__dict__["name"] in [t.__dict__["name"] for t in self.tasks]:
            raise AttributeError("task already exists")
        if task.__dict__["dependencies"]:
            for dependency in task.__dict__["dependencies"]:
                # print([task.__dict__["name"] for task in self.tasks])
                if dependency["task"] not in [task.__dict__["name"] for task in self.tasks]:
                    raise AttributeError("dependency not fulfilled")
        self.task_name_counter += 1
        # self.tasks.append(task.__dict__)
        self.tasks.append(task)

    def getTask(self, taskname):
        """
        Retrieve from the workflow a pav.Task object from a given task name

        Parameters
        ----------
        taskname : str
            The name of the task we want to find in the workflow

        Returns
        -------
        tasks[0] : <class 'pav.Task'>
            Returns the first found task
        None : Nonetype
            If no task was found then returns None

        Example
        -------
        t1 = Task(name="task_one", operator="oph_if", arguments=None)
        task = w1.getTask(taskname="task_one")
        """
        tasks = [t for t in self.tasks if t["name"] == taskname]
        if len(tasks) == 1:
            return tasks[0]
        elif len(tasks) == 0:
            return None

    def save(self, workflowname):
        """
        Save the workflow in a JSON file

        Parameters
        ----------
        workflowname : str
            A name for the workflow which will be used to save it in a JSON file

        Example
        -------
        from pav import *
        w1 = Workflow(name="sample name", author="sample author", abstract="sample abstract")
        w1.save("sample_workflow")

        Raises
        ------
        AttributeError
            If worfklowname, which is the variable of the file, is not a string or it's empty
        """
        import json
        import os
        if not isinstance(workflowname, str):
            raise AttributeError("workflowname must be string")
        if len(workflowname) == 0:
            raise AttributeError("workflowname must contain more than 1 characters")
        data = dict(self.__dict__)
        if "task_name_counter" in data.keys():
            del data["task_name_counter"]
        if not workflowname.endswith(".json"):
            workflowname += ".json"
        data["tasks"] = [t.__dict__ for t in self.tasks]
        with open(os.path.join(os.getcwd(), workflowname), 'w') as fp:
            json.dump(data, fp, indent=4)

    def newTask(self, operator, arguments={}, dependencies={}, name=None, **kwargs):
        """
        Adds a new Task in the workflow without the need of creating a pav.Task object

        Attributes
        ----------
        operator : str
            Ophidia operator name
        arguments : dict
            dict of user-defined operator arguments as key=value pairs
        dependencies : dict
            a dict of dependencies for the task
        name : str
            the name of the task
        on_error : str, optional
            behaviour in case of error
        on_exit : str, optional
            operation to be executed on output objects
        run : str, optional
            enable submission to analytics framework, yes or no

        Returns
        -------
        t : <class 'pav.Task'>
            Returns the task that was created and added to the workflow

        Raises
        ------
        AttributeError
            Raises an AttributeError if the given arguments are not on the task's attributes

        Example
        -------
        w1 = Workflow(name="PTA", author="CMCC Foundation", abstract="sample abstract")
        t1 = w1.newTask(operator='oph_createcontainer', arguments={'container': 'work'}, dependencies={})
        """

        def parameter_check(operator, arguments, dependencies, name):
            if not isinstance(operator, str):
                raise AttributeError("operator must be a string")
            if not isinstance(arguments, dict):
                raise AttributeError("arguments must be a dict")
            if not isinstance(dependencies, dict):
                raise AttributeError("dependencies must be a dict")
            if not isinstance(name, str) and name!=None:
                raise AttributeError("name must be a string")

        parameter_check(operator, arguments, dependencies, name)
        t = Task(operator=operator, arguments=arguments, name=name)
        if dependencies:
            for k in dependencies.keys():
                if dependencies[k]:
                    t.addDependency(task=k, argument=dependencies[k])
                else:
                    t.addDependency(task=k)
        for k in kwargs.keys():
            if k not in self.task_attributes:
                raise AttributeError("Unknown Task argument: {0}".format(k))
        t.__dict__.update(kwargs)
        self.addTask(t)
        return t

    def newSubWorkflow(self, workflow, params, dependency={}, name=None):
        """
        Embeds a workflow into another workflow

        Parameters
        ----------
        workflow : <class 'pav.Workflow'>
            The workflow we will embed to our main workflow
        params : dict of keywords
            a dict of keywords that will be used to replace placeholders in the tasks
        dependency : list
            a list of dependencies
        name : str
            unique name for the workflow's tasks

        Returns
        -------
        A list of the tasks

        Raises
        ------
        AttributeError
            Raises AttributeError when there's an error with the workflows (same name or non-existent), or when the
            dependencies are not fulfilled

        Example
        -------
        w1 = Workflow(name="PTA", author="CMCC Foundation", abstract="sample abstract")
        w2 = Workflow(name="PTA_template", author="CMCC Foundation", abstract="sample abstract")
        t1 = w2.newTask(operator='oph_if')
        task_array = w1.newSubWorkflow(name="new_subworkflow", workflow=w2, params={}, depdnency=[])
        task_array_2 = w1.newSubWorkflow(name="new_subworkflow_2", workflow=w2, params={}, depdnency=[])
        """
        def parameter_check(params, dependency, name):
            if not isinstance(params, dict):
                raise AttributeError("params must be dict")
            if not isinstance(dependency, dict):
                raise AttributeError("dependency must be dict")
            if not isinstance(name, str):
                raise AttributeError("name must be string")

        def validate_workflow(w1, w2):
            if not isinstance(w2, Workflow) or w1.name == w2.name:
                raise AttributeError("Wrong workflow or same workflows")

        def dependency_check(dependency):
            if not isinstance(dependency, dict):
                raise AttributeError("dependency must be a list")
            if len(dependency.keys()) > 2:
                raise AttributeError("Wrong dependency arguments")
            elif len(dependency.keys()) == 2:
                if ("task" not in dependency.keys()) or ("argument" not in dependency.keys()):
                    raise AttributeError("Wrong dependency arguments")
            else:
                if "task" not in dependency.keys():
                    raise AttributeError("Wrong dependency arguments")

        def find_root_tasks_add_dependencies(task, dependencies, new_task):
            if len(task.dependencies) == 0:
                for dependency in dependencies:
                    dependency_check(dependency)
                    if len(dependency.keys()) == 1:
                        new_task.addDependency(task=dependency["task"])
                    else:
                        new_task.addDependency(task=dependency["task"], argument=dependency["argument"])

        def add_dependencies(task, new_task, prefix):
            if len(task.dependencies) > 0:
                for d in task.dependencies:
                    dep_dict = dict(d)
                    dep_dict["task"] = fix_dependency_name(d["task"], prefix)
                    new_task.copyDependency(dep_dict)

        def fix_dependency_name(dependency_name, prefix):
            return "{0}_{1}".format(prefix, dependency_name)

        def add_task_name(given_name, previous_name, task_id):
            if given_name:
                return "{0}_{1}".format(given_name, previous_name)
            else:
                return "{0}_{1}_{2}".format(self.name, str(task_id), previous_name)

        def check_replace_args(params, task_arguments):
            import re
            new_task_arguments = {}
            for k in task_arguments:
                if re.search('(\$.*)', k):
                    if re.findall('(\$.*)', k)[0] in params.keys():
                        new_task_arguments[re.sub("(\$.*)", params[re.findall('(\$.*)', k)[0]], k)] = task_arguments[k]
                    else:
                        new_task_arguments[k] = task_arguments[k]
                else:
                    new_task_arguments[k] = task_arguments[k]
            for k in task_arguments:
                if re.search('(\$.*)', task_arguments[k]):
                    if re.findall('(\$.*)', task_arguments[k])[0] in params.keys():
                        new_task_arguments[k] = re.sub("(\$.*)", params[re.findall('(\$.*)', task_arguments[k])[0]],
                                                       task_arguments[k])
                    else:
                        new_task_arguments[k] = task_arguments[k]
                else:
                    new_task_arguments[k] = task_arguments[k]

            return new_task_arguments
        parameter_check(params, dependency, name)
        validate_workflow(self, workflow)
        task_id = 1
        all_tasks = []
        non_leaf_tasks = []
        for task in workflow.tasks:
            new_task_name = add_task_name(name, task.name, task_id)
            task_id += 1
            new_arguments = check_replace_args(params, task.reverted_arguments())
            new_task = Task(operator=task.operator, arguments=new_arguments, name=new_task_name)
            find_root_tasks_add_dependencies(task, dependency, new_task)
            add_dependencies(task, new_task, name)
            all_tasks.append(new_task)
            self.addTask(new_task)
            non_leaf_tasks += [t["task"] for t in task.dependencies]

        return [t for t in all_tasks if t.name not in non_leaf_tasks]

    @staticmethod
    def load(file):
        """
        Load a workflow from a JSON file

        Parameters
        ----------
        file : str
            the name of the file we want to load

        Returns
        -------
        workflow : <class 'pav.Workflow'>
            Returns the workflow object as it was loaded from the file

        Raises
        ------
        IOError
            Raises IOError if the file doesn't exist
        JSONDecodeError
            Raises JSONDecodeError if the file doesn't containt a valid JSON structure

        Example
        -------
        w1 = workflow.load("json_file.json")
        """

        def file_check(filename):
            import os
            import json
            if not os.path.isfile(filename):
                raise IOError("File does not exist")
            else:
                try:
                    with open(filename, "r") as f:
                        return json.loads(f.read())
                except json.decoder.JSONDecodeError:
                    raise ValueError("File is not a valid JSON")

        def check_workflow_name(data):
            if "name" not in data.keys():
                raise AttributeError("Workflow doesn't have a key")

        def start_workflow(data):
            workflow = Workflow(name=data["name"])
            del data["name"]
            attrs = {k: data[k] for k in data if k != "name" and k != "tasks"}
            workflow.__dict__.update(attrs)
            for d in data["tasks"]:
                new_task = Task(operator=d["operator"], name=d["name"],
                                arguments={a.split("=")[0]: a.split("=")[1] for a in d["arguments"]})
                new_task.__dict__.update({k: d[k] for k in d if k != "name" and k != "operator" and k != "arguments"})
                workflow.addTask(new_task)
            return workflow

        data = file_check(file)
        check_workflow_name(data)
        workflow = start_workflow(data)
        return workflow


class Task:
    """
    Creates a Task object that will be used to be embedded on the workflow

    Construction::
    t1 = Task(name="Sample name", operator="oph_createcontainer", arguments=['container=work', 'dim=lat|lon|time',
        'dim_type=double|double|double', 'hierarchy=oph_base|oph_base|oph_time', 'base_time=1976-01-01',
        'calendar=standard', 'units=d'], on_error="skip")

    Parameters
    ----------
    operator : str
        Ophidia operator name
    arguments : dict
        list of user-defined operator arguments as key=value pairs
    name : str
        unique task name
    type : str
        type of the task
    run : str, optional
        enable submission to analytics framework, yes or no
    on_error : str, optional
        behaviour in case of error
    on_exit : str, optional
        operation to be executed on output objects
    """
    attributes = ["run", "on_exit", "on_error"]
    active_attributes = ["name", "operator", "arguments"]

    def __init__(self, operator, arguments={}, name=None, type=None, **kwargs):
        for k in kwargs.keys():
            if k not in self.attributes:
                raise AttributeError("Unknown Task argument: {0}".format(k))
        self.type = type if type else "ophidia"
        self.name = name
        self.operator = operator
        self.arguments = ["{0}={1}".format(k, arguments[k]) for k in arguments.keys()]
        self.dependencies = []
        self.__dict__.update(kwargs)

    def deinit(self):
        """
        Reverse the initialization of the object
        """
        for k in self.active_attributes:
            self.__delattr__(k)

    def addDependency(self, task, argument=None):
        """
        Adds previous tasks as a dependency on the current task

        Parameters
        ----------
        task : pav.Task
            task name the current argument depends on
        argument : str
            argument depending on the output of the task 'task'

        Raises
        ------
        AttributeError
            When one of the parameters has the wrong type

        Example
        -------
        t2 = w2.newTask(operator='oph_if')
        t3 = Task(name="Create Historical Container", operator="oph_createcontainer", arguments={}, on_error="skip")
        t3.addDependency(t2)
        """
        def parameter_check(task, argument):
            if not isinstance(argument, str):
                raise AttributeError("argument must be string")
            if not isinstance(task, Task):
                raise AttributeError("task must be Task object")

        parameter_check(task, argument)
        dependency_dict = {}
        if not argument:
            dependency_dict["type"] = "embedded"
        else:
            dependency_dict["argument"] = argument
            dependency_dict["type"] = "all"
        dependency_dict["task"] = task.__dict__["name"]
        self.dependencies.append(dependency_dict)

    def copyDependency(self, dependency):
        """
        Copy a dependency instead of using addDependency, when it has the proper format

        Parameters
        ----------
        dependency : dict
            Copy a dependency to a task
        """
        self.dependencies.append(dependency)

    def reverted_arguments(self):
        """
        Changes the format of the arguments

        Returns
        -------
        arguments : dict
            returns the arguments with the newest format
        """
        arguments = {}
        for arg in self.arguments:
            arguments[arg.split("=")[0]] = arg.split("=")[1]
        return arguments
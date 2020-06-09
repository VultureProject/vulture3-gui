---
title: "Application management via API"
currentMenu: vulture_api
parentMenu: app
---

## Overview

The Vulture REST API contains a small set of simple functions allowing modifications on applications/models.

It follows this convention:

```
<ROOT>/api/rest/app/<OPERATION>/<OPTIONS>/
```

**(Please note the ending slash ("`/`") at the end)**

For instance, if the user wants to list the names of all the applications he created, the following can be entered on a UNIX shell:

```
curl --ssl -k -E /var/db/mongodb/mongod.pem 'https://localhost:8000/api/rest/app/list/all/name/'
```

The Vulture REST API introduces models for applications. A model is a special application used to generate other applications. It cannot be enabled.

## Application listing

First, the Vulture REST API provides some listing functions, letting the user know about the applications state.

### Listing all applications and models

To list all the existing applications (and models), the following must be entered:

```
<ROOT>/api/rest/app/list/all/
```

### Listing all applications

To list all the applications (not models), enter the following:

```
<ROOT>/api/rest/app/list/application/
```

### Listing all models

This line will list all the existing models:

```
<ROOT>/api/rest/app/list/model/
```

### Getting an application or a model by its name

Enter the following to get an application or a model by its name:

```
<ROOT>/api/rest/app/list/name/<NAME_TO_ENTER>/
```

### Getting one or several applications/models, given a REGEX

You can also get applications or models with a REGEX:

```
<ROOT>/api/rest/app/list/regex/<REGEX_TO_ENTER>/
```

Currently, the REGEX provided can only contain the following characters:
 - The alphanumeric characters (from "`a`" to "`z`", "`A`" to "`Z`" and "`0`" to "`9`")
 - Underscores ("`_`")
 - Hash characters ("`#`")
 - Spaces ("` `")

Special characters must be encoded accordingly: "`%20`" for spaces, and "`%23`" for hashes.

### Filtering the fields

All requests shown above can contain an option allowing the user to filter the fields returned. For example, the following request returns the name of the application **MyApp**:

```
<ROOT>/api/rest/app/list/name/MyApp/name/
```

If the user wants to filter several fields, a pipe ("`|`") character can be given between each field. For instance, the following request returns the same result than before, adding an extra field showing the different listeners of the application **MyApp**:

```
<ROOT>/api/rest/app/list/name/MyApp/name|listeners/
```

## Application/Model generation

Applications and models can be generated from a given model using this POST request:

```
<ROOT>/api/rest/app/generate/

{
    "model": "<MODEL_NAME>",
    <OPTION #1>,
    .
    .
    .
    <OPTION #N>
}
```

Options are given to customize the generated application. For instance, this POST request generates a new enabled application named **MyApp** from a model **MyModel**, with a different public name:

```
<ROOT>/api/rest/app/generate/

{
    "model": "MyModel",
    "name": "MyApp",
    "enabled": true,
    "public_name": "myapp.lan"
}
```

The default behavior will create a disabled application (and not a model).

For example, the following POST request will generate a disabled application named `<MODEL_NAME>_copy_<RANDOM_STRING>` (since no name was given, a random one is provided instead):

```
<ROOT>/api/rest/app/generate/

{
    "model": "<MODEL_NAME>"
}
```

Finally, an extra option named **reload** can be provided in the URL to reload the newly created application:

```
<ROOT>/api/rest/app/generate/reload/

{
    "model": "<MODEL_NAME>"
}
```

Please note that reference fields cannot be modified at the current time.

## Application/Model updating

Applications and models can be modified with a POST request, similar to the one used to generate new applications:

```
<ROOT>/api/rest/app/update/<APPLICATION_NAME_TO_UPDATE>/

{
    <OPTION #1>,
    .
    .
    .
    <OPTION #N>
}
```

For example, the following request will modify the application named **MyApp**, changing its name to **MyUpdatedApp** and its public name to **myupdatedapp.lan**:

```
<ROOT>/api/rest/app/update/MyApp/

{
    "name": "MyUpdatedApp",
    "public_name": "myupdatedapp.lan"
}
```

Please note that reference fields cannot be modified at the current time.

## Application/Model deletion

An application or a model can be deleted with the following request:

```
<ROOT>/api/rest/app/delete/<APPLICATION_NAME_TO_DELETE>/
```

As an example, this POST request will delete the application named **MyApp**:

```
<ROOT>/api/rest/app/delete/MyApp/
```

**BE CAREFUL**, an application or a model deleted cannot be restored.

## Miscellaneous

### Statistics

Various stats can be provided concerning the applications with the following request:

```
<ROOT>/api/rest/app/stats/
```

Currently, it returns the count number of the models and applications:

```
{
    "models": 3, 
    "applications": {
        "total": 12, 
        "enabled": 8, 
        "not_enabled": 4
    }, 
    "total": 15
}
```
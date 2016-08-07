# Ichiba

Market for tasks.

*Idea*: Declare which task you want to be done and have the market do it.

# Currently supported tasks

## Gofed

* Spec file generator
* Source code analysis

# Technologies

The Ichiba is built over kubernetes.
Ichiba client generates a kubernetes job specification based on a requested tasks.
The tasks includes collection of job logs and upload of results to publicly available site.

# Examples

```sh
$ ichiba -v gofed repo2spec --detect github.com/golang/sys
Generating job specification...
Publishing job on 'global' market
Job has been published (this may be safely interrupted)...
```

Cost Management
===============

The cost of using the Aletheia library is composed a two different components:

1. Cloud Storage costs
2. Cloud KMS keys and operations

All calculations are based on the `current pricing`_.


Cloud Storage
-------------

The cost of Google Cloud Storage is dependent on how redundant the data is.
If we assume we want the highest level of availability and durability for
all secrets, then a secret, average 1kiB would cost $0.000000026 per month,
and $0.000004 per retrieval, or effectively zero.


Cloud KMS
---------

Cloud KMS has two costs for it's use. The first is a per-key cost per month,
and the other is the actual operations that are performed.  The project costs
can be calculated as follows:

* $0.06/mo per chest
* $.000003/operation


Total Cost
----------
Assuming the project has 20 secrets, and has to unwrap them ten times a day,
the cost of using Aletheia would be:

    0.06 + (20 * (0.000000026 + (30 * (10 * (0.000003 + $0.000004))))) = $0.10200052

Or, just more than 10 cents per month at list prices.

.. _current pricing: https://cloud.google.com/pricing

"""
etl_job.py
~~~~~~~~~~

This Python module contains an example Apache Spark ETL job definition
that implements best practices for production ETL jobs. It can be
submitted to a Spark cluster (or locally) using the 'spark-submit'
command found in the '/bin' directory of all Spark distributions
(necessary for running any Spark job, locally or otherwise). For
example, this example script can be executed as follows,

    $SPARK_HOME/bin/spark-submit \
    --master spark://localhost:7077 \
    --py-files packages.zip \
    --files configs/etl_config.json \
    jobs/etl_job.py

where packages.zip contains Python modules required by ETL job (in
this example it contains a class to provide access to Spark's logger),
which need to be made available to each executor process on every node
in the cluster; etl_config.json is a text file sent to the cluster,
containing a JSON object with all of the configuration parameters
required by the ETL job; and, etl_job.py contains the Spark application
to be executed by a driver process on the Spark master node.

"""

from dependencies.etlcomponents import *
from dependencies.spark import start_spark


class Executor(object):
    def __init__(self, spark, log, tasks=[], environment='local'):
        self.tasks = tasks
        self.spark = spark
        self.log = log
        self.environment = environment

    def run(self):

        for task in self.tasks:
            if isinstance(task, Extract):
                df = task.execute(self.spark)
                self.log.warn("Extract completed")
            if isinstance(task, Transform):
                df = task.execute(self.spark)
                self.log.warn("Transform completed")
            if isinstance(task, Load):
                task.execute(self.spark, df, self.environment)
                self.log.warn("Load completed")
            if isinstance(task, Impala) and self.environment != "local":
                task.impala_refresh()


def main():
    """Main ETL script definition.

    :return: None
    """
    # start Spark application and get Spark session, logger and config
    spark, log, config, environment = start_spark(
        app_name='my_etl_job',
        # files=['JobRPM001_config.json', 'transformation.sql']
        )
        # files=['configs/JobRPM001_config.json', 'configs/transformation.sql'])
        # files=['configs/etl_config.json', 'configs/transformation.sql']


    # log that main ETL job is starting
    log.warn('etl_job is up-and-running')
    df = spark.read.format("avro").load("configs/account_id_schema_new.avro")
    df.write.format("avro").save("namesAndFavColors.avro")
    # df.select("name", "favorite_color").write.format("avro").save("namesAndFavColors.avro")

    # Create ETL Components
    print("config:",config)
    try:
        tasks = [Extract(config['extract']), Transform(config['transform']), Load(config['load']), Impala(config['impala'])]
    except KeyError as e:
        print("Some component missing: " + repr(e))

    Executor(spark, log, tasks, environment).run()

    # log the success and terminate Spark application
    log.warn('etl_job is finished')
    spark.stop()
    return None


# entry point for PySpark ETL application
if __name__ == '__main__':

    from os import listdir
    from os.path import isfile, join
    onlyfiles = [f for f in listdir('./') if isfile(join('./', f))]
    print(onlyfiles)
    main()

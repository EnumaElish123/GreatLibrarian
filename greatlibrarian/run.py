from greatlibrarian.Runner import AutoRunner, UpdateRunner
import click
from greatlibrarian.register import register
import importlib.util
import os


@click.command()
@click.option(
    "--testcase_path",
    default=r"E:\GL实验\GL\Datasets\Open-LLMEval\CMMLU-reasoning",
    help="testcase的json文件所存放的文件夹路径",
)
@click.option(
    "--config_path",
    default=r"E:\GL实验\GL\register_usr.py",
    help="配置文件的绝对路径",
)
@click.option("--project_name", default="", help="项目名称，默认为空字符串")
@click.option("--test_name", default="", help="实验名称，默认为空字符串")
@click.option("--test_id", default="", help="实验ID，默认为空字符串")
@click.option("--logs_path", default="", help="日志路径")
def main(
    testcase_path, config_path, project_name, test_id, test_name, logs_path
) -> None:
    spec = importlib.util.spec_from_file_location("conf", config_path)
    conf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf_module)
    config = conf_module.config
    Regis = register(config)
    testcase = testcase_path
    if Regis.checkllm():
        runner = AutoRunner(
            config, testcase, project_name, test_id, test_name, logs_path
        )
        runner.run()
    else:
        error_message = "The __call__ function of your LLM can't work properly!"
        raise Warning(error_message)


@click.command()
@click.option(
    "--config_path",
    default=r"E:\GL实验\GL\register_usr.py",
    help="配置文件的绝对路径",
)
@click.option("--test_id", default="", help="实验ID，默认为空字符串")
@click.option("--logs_path", default="", help="日志路径")
def update(config_path, test_id, logs_path) -> None:
    path = os.path.join(logs_path, "Logs")
    if os.path.exists(os.path.join(path, test_id)):
        spec = importlib.util.spec_from_file_location("conf", config_path)
        conf_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conf_module)
        config = conf_module.config
        runner = UpdateRunner(config, test_id, path)
        runner.run()
    else:
        error_message = "Files not Found! Please use gltest before glupdate."
        raise Warning(error_message)


if __name__ == "__main__":
    main()

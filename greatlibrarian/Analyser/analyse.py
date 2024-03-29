import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
from ..Utils import extract_mistaken_info, extract_example_info
import matplotlib
import textwrap
from matplotlib import rcParams
import warnings
from typing import Tuple, List, Union
import re
from datetime import datetime


# log_name = generate_name_new('analyse')
# log_name = "analyse"
# logger_name = "analyse.log"
# if Test_ID == '':
#     logger_subfile = generate_logger_subfile()
# else:
#     logger_subfile = Test_ID
# add_logger_to_class = add_logger_name_cls(
#     log_name, os.path.join("Logs", logger_subfile)
# )
# logger_path = os.path.join(os.path.join("Logs", logger_subfile))


# @add_logger_to_class
class Analyse:
    """A class to do the analysis after the interaction."""

    def __init__(self, score_dict) -> None:
        self.score_dict = score_dict

    def analyse(
        self,
    ) -> Tuple[str, str, List[Union[List[str], List[float], List[int]]]]:
        """
        A function to analyse the score that LLM gets in the testproject, including many testcases.
        The information used for analysis comes from the function get_eval_result in class getinfo.
        By reading the information(a dictionary) provided by the function get_eval_result, this function will create a new log file and write the analysis in it.
        The average score that the LLM gets in the testcase will be recorded, and finally the function will give an overall evaluation of the LLM.
        The log file generated by this function is formatted like:
        "By 'keywords' evaluation, the LLM gets XX(0-1) scores on average.
        By 'toolUsage' evaluation, the LLM gets XX(0-1) scores on average.
        By 'LLMEval' evaluation, the LLM gets XX(0-1) scores on average.
        To conclude, the LLM …"
        """

        score = self.score_dict
        score_list = []
        score_mean = [0] * len(score)
        score_get = [0] * len(score)
        field_list = list(score.keys())
        total_score = [0] * len(score)

        for i in range(len(score)):
            score_list.append(score[field_list[i]])

        for i in range(len(score)):
            if score_list[i] == []:
                score_mean[i] = "Not evaluated in this field"
            else:
                score_mean[i] = float(
                    "%.3f" % (sum(score_list[i]) / len(score_list[i]))
                )
                total_score[i] = len(score_list[i])
                score_get[i] = float("%.3f" % (sum(score_list[i])))
        get_score_info = ""

        for i in range(len(score)):
            get_score_info += f'\nIn {field_list[i]} field, the LLM gets "{score_get[i]}/{total_score[i]}" scores.\n'

        plotinfo = [field_list, score_get, total_score]

        mean_score_list = []
        for scores in score_mean:
            if scores != "Not evaluated in this field":
                if scores >= 0.6:
                    mean_score_list.append("does well in")
                else:
                    mean_score_list.append("is not good at")
            else:
                mean_score_list.append("is not evaluated")
        conclude_info = "To conclude:\n"
        for i in range(len(score)):
            conclude_info += (
                f"\nThe model {mean_score_list[i]} in {field_list[i]} field.\n"
            )
        print(get_score_info)
        print(conclude_info)
        return (get_score_info, conclude_info, plotinfo)

    def report(self, plotinfo, llm_intro, log_path, report_path) -> None:
        """
        log_path: The path of the dialog_init.log
        logger_path: the path to the analyse.log
        """
        field = plotinfo[0]
        score_get = plotinfo[1]
        total_score = plotinfo[2]
        totalnum = sum(total_score)

        plt.rcParams["font.size"] = 18
        plt.rcParams["text.usetex"] = False

        pdf_name = self.generate_new_name(report_path, "report")
        pdf_file_path = os.path.join(report_path, pdf_name)

        pdf_pages = PdfPages(pdf_file_path)

        # filtered_fields = [
        #     fields
        #     for fields, total_scores in zip(field, total_score)
        #     if total_scores > 0
        # ]

        # filtered_totalscore = [
        #     totalscores for totalscores in total_score if totalscores > 0
        # ]
        # filtered_score_get = [
        #     score
        #     for score, total_scores in zip(score_get, total_score)
        #     if total_scores > 0
        # ]

        # 1.背景介绍
        fig = plt.figure(figsize=(30, 30))
        plt.rcParams["font.sans-serif"] = ["SimSun"]
        plt.rcParams["mathtext.fontset"] = "stix"
        plt.rcParams["text.usetex"] = False

        title = "1.背景介绍"
        plt.title(title, fontsize=32, ha="center", y=1.1, fontfamily="SimSun")

        intro = self.introduction_of_llm(log_path, llm_intro)

        fig.text(
            0.1, 0.55, intro, fontsize=25, fontfamily="SimSun", ha="left", va="center"
        )
        plt.axis("off")

        # try:
        #     pdf_pages.savefig(fig)
        # except Exception as e:
        #     warning_message = f"Warning: An report exception occurred - {e}"
        #     warnings.warn(warning_message, RuntimeWarning)

        pdf_pages.savefig(fig)

        # 2.测试用例数据信息

        fig, axs = plt.subplots(1, 2, figsize=(30, 30), gridspec_kw={"wspace": 0.15})

        field_info = ""
        if len(field) <= 3:
            for fields in field:
                field_info += f'"{(fields)}"'
            field_info += "领域"
        else:
            for i in range(3):
                field_info += f'"{str(field[i])}"'
            field_info += "等领域。"

        testcasenum_info = ""
        for i in range(len(field)):
            testcasenum_info += f"\n “{field[i]}”领域中有{total_score[i]}条测试用例。\n"
        score_info = ""
        for i in range(len(score_get)):
            score_info += f"\n在“{field[i]}”领域中 ,该大语言模型的得分为: {score_get[i]}/{total_score[i]}。\n"

        time = self.extract_time(log_path)
        time_per_testcase = round(time / totalnum, 3)
        time_info = (
            f"在本次测试中，LLM的响应时间为：平均每条测试用例{time_per_testcase}秒"
        )
        conclude_info = (
            f"本次测试包括{totalnum}条测试用例.\n\n这些测试用例主要包括"
            + field_info
            + f"\n\n在所有测试用例中:\n"
            + testcasenum_info
            + score_info
            + "\n"
            + time_info
        )

        axs[0].text(
            0,
            0.55,
            conclude_info,
            fontsize=25,
            ha="left",
            va="center",
            fontfamily="SimSun",
        )

        axs[0].axis("off")

        rcParams["font.family"] = "SimSun"

        # 饼状图绘制

        percentages = [num / totalnum for num in total_score]
        patches, texts, autotexts = axs[1].pie(
            percentages, labels=field, autopct="%1.1f%%", startangle=140
        )
        for autotext in autotexts:
            autotext.set_size(28)
        for text in texts:
            text.set_size(28)

        axs[1].axis("equal")

        axs[1] = plt.gca()
        axs[1].set_aspect("equal")
        axs[1].set_position([0.0, 1.0, 0.6, 0.6])

        legend_labels = ["{}".format(fields) for fields in field]
        legend = axs[1].legend(
            patches, legend_labels, loc="lower right", bbox_to_anchor=(1.25, 0.10)
        )

        for label in legend.get_texts():
            label.set_fontsize(30)

        axs[1].set_position([0.0, 1.0, 0.6, 0.6])

        axs[1].axis("off")

        plt.subplots_adjust(wspace=0.45)

        title = "2.测试用例数据"
        plt.suptitle(title, fontsize=32, ha="center", y=0.95, fontfamily="SimSun")

        try:
            pdf_pages.savefig(fig)
        except Exception as e:
            warning_message = f"Warning: An report exception occurred - {e}"
            warnings.warn(warning_message, RuntimeWarning)

        # 3.错误的测试用例

        fig = plt.figure(figsize=(30, 30))

        title = "3.回答错误的测试用例"
        plt.rcParams["font.sans-serif"] = ["SimSun"]
        plt.rcParams["mathtext.fontset"] = "stix"
        plt.rcParams["text.usetex"] = False
        plt.title(title, fontsize=32, ha="center", y=1.1, fontfamily="SimSun")

        mistaken_list = extract_mistaken_info(log_path)
        mistaken_txt = ""

        for i in range(len(mistaken_list)):
            mistaken_list[i][0] = textwrap.fill(mistaken_list[i][0], width=68)
            mistaken_list[i][1] = textwrap.fill(mistaken_list[i][1], width=68)

        if len(mistaken_list) <= 4:
            for mistakens in mistaken_list:
                if len(mistakens) == 5:
                    mistakens[0] = self.escape_latex_special_characters(mistakens[0])
                    mistakens[1] = self.escape_latex_special_characters(mistakens[1])
                    if mistakens[2]:
                        mistaken = f'\n\n对于以下这条属于"{mistakens[2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistakens[0]}”\n\n回答：“{mistakens[1]}”\n\n该问题的正确答案应包含关键字：{mistakens[3]},不应包含黑名单：{mistakens[4]}。\n\n\n'
                    else:
                        mistaken = f'\n\n对于以下这条属于"{mistakens[2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistakens[0]}”\n\n回答：“{mistakens[1]}”\n\n该问题的正确答案应包含关键字：{mistakens[3]},不应包含黑名单：{mistakens[4]}。\n\n\n'
                    mistaken_txt += mistaken
                else:
                    mistakens[0] = self.escape_latex_special_characters(mistakens[0])
                    mistakens[1] = self.escape_latex_special_characters(mistakens[1])
                    if mistakens[2]:
                        mistaken = f'\n\n对于以下这条属于"{mistakens[2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistakens[0]}”\n\n回答：“{mistakens[1]}”\n\n该问题的正确答案应包含关键字：{mistakens[3]}。\n\n\n'
                    else:
                        mistaken = f'\n\n对于以下这条属于"{mistakens[2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistakens[0]}”\n\n回答：“{mistakens[1]}”\n\n该问题的正确答案应包含关键字：{mistakens[3]}。\n\n\n'
                    mistaken_txt += mistaken
        else:
            for i in range(4):
                if len(mistaken_list[i]) == 5:
                    mistaken_list[i][0] = self.escape_latex_special_characters(
                        mistaken_list[i][0]
                    )
                    mistaken_list[i][1] = self.escape_latex_special_characters(
                        mistaken_list[i][1]
                    )
                    if mistaken_list[i][2]:
                        mistaken = f'\n\n对于以下这条属于"{mistaken_list[i][2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistaken_list[i][0]}”\n\n回答：“{mistaken_list[i][1]}”\n\n该问题的正确答案应包含关键字：{mistaken_list[i][3]},不应包含黑名单：{mistaken_list[i][4]}。\n\n\n'
                    else:
                        mistaken = f'\n\n对于以下这条属于"{mistaken_list[i][2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistaken_list[i][0]}”\n\n回答：“{mistaken_list[i][1]}”\n\n该问题的正确答案应包含关键字：{mistaken_list[i][3]},不应包含黑名单：{mistaken_list[i][4]}。\n\n\n'
                    mistaken_txt += mistaken
                else:
                    mistaken_list[i][0] = self.escape_latex_special_characters(
                        mistaken_list[i][0]
                    )
                    mistaken_list[i][1] = self.escape_latex_special_characters(
                        mistaken_list[i][1]
                    )
                    if mistaken_list[i][2]:
                        mistaken = f'\n\n对于以下这条属于"{mistaken_list[i][2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistaken_list[i][0]}”\n\n回答：“{mistaken_list[i][1]}”\n\n该问题的正确答案应包含关键字：{mistaken_list[i][3]}。\n\n\n'
                    else:
                        mistaken = f'\n\n对于以下这条属于"{mistaken_list[i][2]}"领域的问题，该大语言模型的回答出现了错误。\n\n问题：“{mistaken_list[i][0]}”\n\n回答：“{mistaken_list[i][1]}”\n\n该问题的正确答案应包含关键字：{mistaken_list[i][3]}。\n\n\n'
                    mistaken_txt += mistaken
        if mistaken_txt == "":
            mistaken_txt += (
                "该LLM完全通过了本次测试，正确回答了所有的测试用例，无错误用例。"
            )

        fig.text(
            0.1,
            0.55,
            mistaken_txt,
            fontsize=25,
            fontfamily="SimSun",
            ha="left",
            va="center",
        )

        plt.axis("off")

        # try:
        #     pdf_pages.savefig(fig)
        # except Exception as e:
        #     warning_message = f"Warning: An report exception occurred - {e}"
        #     warnings.warn(warning_message, RuntimeWarning)

        pdf_pages.savefig(fig)
        # 4.测试的各领域的得分率柱状图

        accuracies = []
        labels = []

        for score, total in zip(score_get, total_score):
            if total == 0:
                continue
            else:
                accuracy = (score / total) * 100
                label = f"{accuracy:.2f}%"
            accuracies.append(accuracy)
            labels.append(label)

        plt.figure(figsize=(30, 30))
        plt.rcParams["mathtext.fontset"] = "stix"
        matplotlib.rcParams["axes.unicode_minus"] = False
        bars = plt.bar(field, accuracies)
        plt.xlabel("领域", fontsize=38, fontfamily="SimSun")
        plt.ylabel("得分率", fontsize=38, fontfamily="SimSun")
        plt.title("4.各领域答题得分率", fontsize=32, y=1.15, fontfamily="SimSun")
        plt.xticks(rotation=45, ha="right", fontsize=28, fontfamily="SimSun")
        plt.yticks(fontsize=32)

        y_min, y_max = plt.ylim()
        if y_min < 0:
            plt.ylim(0, y_max)

        for i, (bar, label) in enumerate(zip(bars, labels)):
            plt.text(i, bar.get_height(), label, ha="center", va="bottom", fontsize=43)

        plt.tight_layout()
        try:
            pdf_pages.savefig()
        except Exception as e:
            warning_message = f"Warning: An report exception occurred - {e}"
            warnings.warn(warning_message, RuntimeWarning)

        pdf_pages.close()
        print("Report Generated !")

    def introduction_of_llm(self, log_path, llm_intro) -> str:
        # field_dict = {
        #     "knowledge_understanding": "语言理解",
        #     "coding": "代码",
        #     "common_knowledge": "知识与常识",
        #     "reasoning": "逻辑推理",
        #     "multi_language": "多语言",
        #     "specialized_knowledge": "专业知识",
        #     "traceability": "可追溯性",
        #     "outputformatting": "输出格式化",
        #     "internal_security": "内生安全性",
        #     "external_security": "外生安全性",
        # }
        ex_list = extract_example_info(log_path)

        for i in range(len(ex_list)):
            ex_list[i][0] = textwrap.fill(ex_list[i][0], width=70)
            ex_list[i][1] = textwrap.fill(ex_list[i][1], width=70)

        example_txt = "以下是本次测试中的几条测试用例及其回答：\n\n"

        if len(ex_list) == 0:
            example_txt += "本次测试中，该大语言模型未答对任何问题"

        if len(ex_list) <= 3 and len(ex_list) > 0:
            for ex in ex_list:
                ex[0] = self.escape_latex_special_characters(ex[0])
                ex[1] = self.escape_latex_special_characters(ex[1])
                example = (
                    "\n\n"
                    + f'对于以下这条属于"{ex[2]}"领域的问题，该大语言模型的回答完全正确。'
                    + "\n\n"
                    + f"问题：“{ex[0]}”"
                    + "\n\n"
                    + f"回答：“{ex[1]}”"
                    + "\n\n"
                )
                example_txt += example
        if len(ex_list) > 3:
            for i in range(3):
                ex_list[i][0] = self.escape_latex_special_characters(ex_list[i][0])
                ex_list[i][1] = self.escape_latex_special_characters(ex_list[i][1])
                example = (
                    "\n\n"
                    + f'对于以下这条属于"{ex_list[i][2]}"领域的问题，该大语言模型的回答完全正确。'
                    + "\n\n"
                    + f"问题：“{ex_list[i][0]}”"
                    + "\n\n"
                    + f"回答：“{ex_list[i][1]}”"
                    + "\n\n"
                )
                example_txt += example

        intro = "这是一个对于场景化大语言模型的自动化测评报告。\n\n由于工具中暂无关于当前大语言模型的背景信息，所以当前页仅展示本次测评中大语言模型答对的数条测试样例。"

        if llm_intro != "":
            llm_intro = "\n\n".join(
                [
                    textwrap.fill(paragraph, width=76)
                    for paragraph in llm_intro.split("\n\n")
                ]
            )
            intro = llm_intro
            intro += "\n\n本次对该大语言模型的测试涉及多个领域的问题，测试的结果和分析如下文所示。\n\n"
            intro += example_txt
        return intro

    def generate_new_name(self, folder_path, base_name):
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        version_numbers = [
            int(re.search(rf"{base_name}-v(\d+).pdf", f).group(1))
            for f in pdf_files
            if re.match(rf"{base_name}-v\d+.pdf", f)
        ]
        max_version = max(version_numbers) if version_numbers else 0
        new_name = f"{base_name}-v{max_version + 1}.pdf"
        return new_name

    def extract_time(self, log_path):
        with open(log_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        time_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

        all_times = []

        for line in lines:
            time_match = time_pattern.search(line)
            if time_match:
                time_str = time_match.group(0)
                time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                all_times.append(time_obj)

        if all_times:
            min_time = min(all_times)
            max_time = max(all_times)

            time_difference = max_time - min_time
            return time_difference.total_seconds()
        else:
            return None

    def escape_latex_special_characters(self, text):
        text = re.sub(r"([#$%&~_^\\{}])", r"\\\1", text)
        return text

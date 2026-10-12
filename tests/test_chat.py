from sqlalchemy.exc import SQLAlchemyError

from src.chat import run_chat


def test_displays_question_and_response_in_portuguese():
    questions = iter(["Qual o faturamento?", EOFError])
    output = []
    answers = []

    def input_fn(prompt):
        assert prompt == "Faça sua pergunta: "
        question = next(questions)
        if question is EOFError:
            raise EOFError
        return question

    def answer_fn(question):
        answers.append(question)
        return "O faturamento foi de 10 milhões de reais."

    exit_code = run_chat(input_fn, output.append, answer_fn)

    assert exit_code == 0
    assert answers == ["Qual o faturamento?"]
    assert output == [
        "PERGUNTA: Qual o faturamento?\nRESPOSTA: O faturamento foi de 10 milhões de reais.",
        "",
    ]


def test_reports_database_errors_and_stops(capsys):
    exit_code = run_chat(
        input_fn=lambda _: "Pergunta",
        output_fn=lambda _: None,
        answer_fn=lambda _: (_ for _ in ()).throw(SQLAlchemyError("database offline")),
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Falha no chat: database offline" in captured.err


def test_skips_empty_questions():
    inputs = iter(["  ", EOFError])
    output = []

    def input_fn(_):
        question = next(inputs)
        if question is EOFError:
            raise EOFError
        return question

    assert run_chat(input_fn, output.append, lambda _: "unexpected") == 0
    assert output == [""]

class ReportCode:
    annual = 1            # 재무제표 연간
    quarter = 2           # 재무제표 분기
    summary_annual = 3    # FnGuide Highlight 연간
    summary_quarter = 4   # FnGuide Highlight 분기


class StatementSector:
    financing = 'financing'
    investment = 'investment'
    income = 'income'
    cash_flow = 'cash_flow'


class StatementType:
    BS = 'BS'
    IS = 'IS'
    CF = 'CF'

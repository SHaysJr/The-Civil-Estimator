from dataclasses import dataclass
from decimal import Decimal
from .money import dec, money


@dataclass(frozen=True)
class CrewMember:
    role_name: str
    count: int
    regular_rate: Decimal
    overtime_rate: Decimal

    @classmethod
    def make(cls, role_name, count, regular_rate, overtime_rate):
        return cls(role_name, int(count), dec(regular_rate), dec(overtime_rate))


def crew_daily_cost(crew, regular_hours=8, overtime_hours=2) -> Decimal:
    total = Decimal('0')
    for member in crew:
        total += member.count * (
            member.regular_rate * dec(regular_hours)
            + member.overtime_rate * dec(overtime_hours)
        )
    return money(total)

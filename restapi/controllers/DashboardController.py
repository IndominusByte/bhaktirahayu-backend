from config import database
from sqlalchemy.sql import select, func
from models.InstitutionModel import institution
from models.LocationServiceModel import location_service
from models.GuardianModel import guardian
from models.UserModel import user
from models.CovidCheckupModel import covid_checkup
from models.ClientModel import client
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class DashboardLogic:
    @staticmethod
    async def get_positive_negative_chart_data(**kwargs) -> tuple:
        query_positive = select([func.count(covid_checkup.c.id)]).where(
            (covid_checkup.c.check_result == 'positive') &
            (covid_checkup.c.checking_type == kwargs['checking_type'])
        )
        query_negative = select([func.count(covid_checkup.c.id)]).where(
            (covid_checkup.c.check_result == 'negative') &
            (covid_checkup.c.checking_type == kwargs['checking_type'])
        )

        if institution_id := kwargs['institution_id']:
            query_positive = query_positive.where(covid_checkup.c.institution_id == institution_id)
            query_negative = query_negative.where(covid_checkup.c.institution_id == institution_id)

        if location_service_id := kwargs['location_service_id']:
            query_positive = query_positive.where(covid_checkup.c.location_service_id == location_service_id)
            query_negative = query_negative.where(covid_checkup.c.location_service_id == location_service_id)

        if kwargs['kind'] == 'week':
            query_positive = query_positive.where(func.date(covid_checkup.c.created_at) == kwargs['days_ago'])
            query_negative = query_negative.where(func.date(covid_checkup.c.created_at) == kwargs['days_ago'])

        if kwargs['kind'] in ['month','year']:
            query_positive = query_positive.where(
                (func.date(covid_checkup.c.created_at) >= kwargs['days_ago']) &
                (func.date(covid_checkup.c.created_at) <= kwargs['days_now'])
            )
            query_negative = query_negative.where(
                (func.date(covid_checkup.c.created_at) >= kwargs['days_ago']) &
                (func.date(covid_checkup.c.created_at) <= kwargs['days_now'])
            )

        return (
            await database.execute(query=query_positive.as_scalar()),
            await database.execute(query=query_negative.as_scalar())
        )

    @staticmethod
    async def get_done_waiting_chart_data(**kwargs) -> tuple:
        query_done = select([func.count(covid_checkup.c.id)]).where(
            (covid_checkup.c.check_date.isnot(None)) &
            (covid_checkup.c.check_result.isnot(None))
        )
        query_waiting = select([func.count(covid_checkup.c.id)]).where(
            (covid_checkup.c.check_date.is_(None)) &
            (covid_checkup.c.check_result.is_(None))
        )

        if institution_id := kwargs['institution_id']:
            query_done = query_done.where(covid_checkup.c.institution_id == institution_id)
            query_waiting = query_waiting.where(covid_checkup.c.institution_id == institution_id)

        if location_service_id := kwargs['location_service_id']:
            query_done = query_done.where(covid_checkup.c.location_service_id == location_service_id)
            query_waiting = query_waiting.where(covid_checkup.c.location_service_id == location_service_id)

        if kwargs['kind'] == 'week':
            query_done = query_done.where(func.date(covid_checkup.c.created_at) == kwargs['days_ago'])
            query_waiting = query_waiting.where(func.date(covid_checkup.c.created_at) == kwargs['days_ago'])

        if kwargs['kind'] in ['month','year']:
            query_done = query_done.where(
                (func.date(covid_checkup.c.created_at) >= kwargs['days_ago']) &
                (func.date(covid_checkup.c.created_at) <= kwargs['days_now'])
            )
            query_waiting = query_waiting.where(
                (func.date(covid_checkup.c.created_at) >= kwargs['days_ago']) &
                (func.date(covid_checkup.c.created_at) <= kwargs['days_now'])
            )

        return (
            await database.execute(query=query_done.as_scalar()),
            await database.execute(query=query_waiting.as_scalar())
        )

class DashboardCrud:
    pass

class DashboardFetch:
    @staticmethod
    async def get_all_total_data() -> dict:
        total_institutions = await database.execute(query=select([func.count(institution.c.id)]).as_scalar())
        total_location_services = await database.execute(query=select([func.count(location_service.c.id)]).as_scalar())
        total_guardians = await database.execute(query=select([func.count(guardian.c.id)]).as_scalar())
        total_doctors = await database.execute(
            query=select([func.count(user.c.id)]).where(user.c.role == 'doctor').as_scalar()
        )
        total_male = await database.execute(
            query=select([func.count(client.c.id)]).where(client.c.gender == 'LAKI-LAKI').as_scalar()
        )
        total_female = await database.execute(
            query=select([func.count(client.c.id)]).where(client.c.gender == 'PEREMPUAN').as_scalar()
        )

        return {
            'total_institutions': total_institutions,
            'total_location_services': total_location_services,
            'total_guardians': total_guardians,
            'total_doctors': total_doctors,
            'total_male': total_male,
            'total_female': total_female
        }

    @staticmethod
    async def get_all_chart_data(**kwargs) -> dict:
        time_now = datetime.now(tz).replace(tzinfo=None)
        result = {'done_waiting': [], 'antigen_p_n': [], 'genose_p_n': [], 'pcr_p_n': []}

        if kwargs['period'] == 'week':
            for i in range(7):
                days_ago = time_now - timedelta(days=i)

                # filter done_waiting
                done, waiting = await DashboardLogic.get_done_waiting_chart_data(**kwargs,kind='week',days_ago=days_ago)
                result['done_waiting'].append({'date': days_ago.strftime("%d %b %Y"), 'done': done, 'waiting': waiting})

                # filter antigen
                antigen_p, antigen_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='week',checking_type='antigen',days_ago=days_ago
                )
                result['antigen_p_n'].append({
                    'date': days_ago.strftime("%d %b %Y"), 'positive': antigen_p, 'negative': antigen_n
                })

                # filter genose
                genose_p, genose_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='week',checking_type='genose',days_ago=days_ago
                )
                result['genose_p_n'].append({
                    'date': days_ago.strftime("%d %b %Y"), 'positive': genose_p, 'negative': genose_n
                })

                # filter pcr
                pcr_p, pcr_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='week',checking_type='pcr',days_ago=days_ago
                )
                result['pcr_p_n'].append({
                    'date': days_ago.strftime("%d %b %Y"), 'positive': pcr_p, 'negative': pcr_n
                })

        if kwargs['period'] == 'month':
            for i in range(1,5):
                days_ago = time_now - timedelta(days=i * 7)
                days_now = time_now - timedelta(days=i * 7 - 7)

                # filter done_waiting
                done, waiting = await DashboardLogic.get_done_waiting_chart_data(
                    **kwargs,kind='month',days_ago=days_ago,days_now=days_now
                )
                result['done_waiting'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'done': done,
                    'waiting': waiting
                })

                # filter antigen
                antigen_p, antigen_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='month',checking_type='antigen',days_ago=days_ago,days_now=days_now
                )
                result['antigen_p_n'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'positive': antigen_p,
                    'negative': antigen_n
                })

                # filter genose
                genose_p, genose_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='month',checking_type='genose',days_ago=days_ago,days_now=days_now
                )
                result['genose_p_n'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'positive': genose_p,
                    'negative': genose_n
                })

                # filter pcr
                pcr_p, pcr_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='month',checking_type='pcr',days_ago=days_ago,days_now=days_now
                )
                result['pcr_p_n'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'positive': pcr_p,
                    'negative': pcr_n
                })

        if kwargs['period'] == 'year':
            for i in range(1,13):
                days_ago = time_now - timedelta(days=i * 30)
                days_now = time_now - timedelta(days=i * 30 - 30)

                # filter done_waiting
                done, waiting = await DashboardLogic.get_done_waiting_chart_data(
                    **kwargs,kind='year',days_ago=days_ago,days_now=days_now
                )
                result['done_waiting'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'done': done,
                    'waiting': waiting
                })

                # filter antigen
                antigen_p, antigen_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='year',checking_type='antigen',days_ago=days_ago,days_now=days_now
                )
                result['antigen_p_n'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'positive': antigen_p,
                    'negative': antigen_n
                })

                # filter genose
                genose_p, genose_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='year',checking_type='genose',days_ago=days_ago,days_now=days_now
                )
                result['genose_p_n'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'positive': genose_p,
                    'negative': genose_n
                })

                # filter pcr
                pcr_p, pcr_n = await DashboardLogic.get_positive_negative_chart_data(
                    **kwargs,kind='year',checking_type='pcr',days_ago=days_ago,days_now=days_now
                )
                result['pcr_p_n'].append({
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'positive': pcr_p,
                    'negative': pcr_n
                })

        return result

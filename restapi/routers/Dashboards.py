from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT
from controllers.DashboardController import DashboardFetch
from schemas.dashboards.DashboardSchema import DashboardTotalData, DasboardChartData
from dependencies.DashboardDependant import get_all_query_dashboard

router = APIRouter()

@router.get('/total-data',response_model=DashboardTotalData)
async def total_data_dashboard(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    return await DashboardFetch.get_all_total_data()

@router.get('/chart-data',response_model=DasboardChartData)
async def chart_data_dashboard(
    query_string: get_all_query_dashboard = Depends(),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    return await DashboardFetch.get_all_chart_data(**query_string)

import asyncio
from fastapi import APIRouter, Depends, WebSocket
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

@router.websocket('/ws-server-info')
async def websocket_server_info(websocket: WebSocket):
    dashboard = websocket.app.state.dashboard
    try:
        await dashboard.connect(websocket)
        while len(dashboard.active_connections) > 0:
            await dashboard.broadcast_server_info()
            await asyncio.sleep(2)
    except Exception:
        await dashboard.disconnect(websocket,'websocket')

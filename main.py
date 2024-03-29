import strawberry
from strawberry.tools import create_type
from strawberry.fastapi import GraphQLRouter

from fastapi import FastAPI

from os import getenv

# override PyObjectId and Context scalars
from models import PyObjectId
from otypes import Context, PyObjectIdType

# import all queries and mutations
from queries_clubs import queries as queries_clubs
from queries_members import queries as queries_members
from mutations_clubs import mutations as mutations_clubs
from mutations_members import mutations as mutations_members


# check whether running in debug mode
DEBUG = int(getenv("GLOBAL_DEBUG", 0))

# create query types
queries = queries_clubs + queries_members
Query = create_type("Query", queries)

# create mutation types
mutations = mutations_clubs + mutations_members
Mutation = create_type("Mutation", mutations)


# override context getter
async def get_context() -> Context:
    return Context()


# initialize federated schema
schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    enable_federation_2=True,
    scalar_overrides={PyObjectId: PyObjectIdType},
)

DEBUG = getenv("SERVICES_DEBUG", "False").lower() in ("true", "1", "t")

# serve API with FastAPI router
gql_app = GraphQLRouter(schema, graphiql=True, context_getter=get_context)
app = FastAPI(
    debug=DEBUG,
    title="CC Clubs Microservice",
    desciption="Handles Data of Clubs and Members",
)
app.include_router(gql_app, prefix="/graphql")

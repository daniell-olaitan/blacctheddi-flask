from sqlmodel import SQLModel


# class BaseSchema(SQLModel):
#     class Config:
#         from_attributes = True

#     def model_dump(self, **kwargs):
#         response_model = getattr(self, "__response_model__", None)
#         data = super().model_dump(**kwargs)

#         if response_model:
#             allowed_fields = set(response_model.model_fields.keys())
#             filtered_data = {}

#             for k, v in data.items():
#                 if k in allowed_fields:
#                     field_type = response_model.model_fields[k].annotation

#                     # If the value is another BaseSchema, recurse
#                     if isinstance(v, BaseSchema):
#                         filtered_data[k] = v.model_dump()

#                     # If the value is a list of BaseSchemas, recurse on each
#                     elif isinstance(v, list) and v and isinstance(v[0], BaseSchema):
#                         filtered_data[k] = [item.model_dump() for item in v]

#                     else:
#                         filtered_data[k] = v
#             return filtered_data

#         return data


class StatusJSON(SQLModel):
    status: str

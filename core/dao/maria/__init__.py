import logging

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def make_query(query_type: str, **kwargs):
    quires = []
    params = []

    for key, value in kwargs.items():
        if value is not None:
            if 'eq' == query_type:
                quires.append(f' and {key} = %s')
            elif 'like' == query_type:
                quires.append(f' and {key} like %s%')
            elif 'in' == query_type:
                raise NotImplementedError
                # placeholder = '%s'
                # param_subs = ','.join((placeholder, ) * len(params))
                # quires.append(f' and {key} in(%s)')
            elif 'text' == query_type:
                raise NotImplementedError
            else:
                raise ValueError(f'Not supported query_type: {query_type}')

            params.append(value)

    return quires, params

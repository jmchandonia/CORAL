from sklearn import decomposition
from generix import services
from generix.brick import Brick, BrickProvenance
from generix.ontology import Term


class PCA:
    def __init__(self, n_components=3, whiten=True):
        self.__pca = decomposition.PCA(
            n_components=n_components, whiten=whiten)
        self.__n_components = n_components
        self.__brick = None
        self.__brick_type_term = services.term_provider.get_term('ME:0000177')
        self.__brick_dim_type_term = services.term_provider.get_term(
            'ME:0000178')
        self.__brick_dim_var_type_term = services.term_provider.get_term(
            'ME:0000178')

    def get_params(self):
        return self.__pca.get_params()

    @property
    def brick_type_term(self):
        return self.__brick_type_term

    @property
    def brick_dim_type_term(self):
        return self.__brick_dim_type_term

    @property
    def brick_dim_var_type_term(self):
        return self.__brick_dim_var_type_term

    @property
    def n_components(self):
        return self.__n_components

    def fit(self, brick, name='PCA'):
        if brick.dim_count != 2:
            raise ValueError('The expectd number of dimensions should be 2')

        dim = brick.dims[0]
        pca_brick = Brick(
            name=name,
            type_term=self.brick_type_term,
            dim_terms=[
                dim.type_term,
                self.brick_dim_type_term
            ],
            shape=[dim.size, self.n_components])

        for data_var in brick.data_vars:
            values = data_var.values
            self.__pca.fit(values)
            pca_values = self.__pca.transform(values)
            pca_brick.add_data_var(
                data_var.type_term, data_var.units_term, pca_values, data_var.scalar_type)

        # populate dims vars
        for var in dim.vars:
            pca_brick.dims[0].add_var(
                var.type_term, var.units_term, var.values, var.scalar_type)

        pca_brick.dims[1].add_var(self.brick_dim_var_type_term, None, [
            'PCA%s' % (i + 1) for i in range(self.n_components)])

        b_prov = brick.get_base_session_provenance()
        prov = BrickProvenance('sklearn.decomposition.PCA',
                               ['n_components:%s' % self.n_components,
                                'dim_index:%s' % 0])
        b_prov.provenance_items.append(prov)
        pca_brick.session_provenance.provenance_items.append(b_prov)
        self.__brick = brick
        self.__dict__['components_'] = self.__build_components_brick()

        return pca_brick

    def __build_components_brick(self):
        dim = self.__brick.dims[1]

        # pca_comp_brick
        pca_comp_brick = Brick(
            name='PCA compoenents',
            type_term=self.brick_type_term,
            dim_terms=[
                dim.type_term,
                self.brick_dim_type_term
            ],
            shape=[dim.size, self.n_components])

        for data_var in self.__brick.data_vars:
            values = data_var.values
            self.__pca.fit(values)
            pca_comp_brick.add_data_var(
                data_var.type_term, data_var.units_term, self.__pca.components_.T, data_var.scalar_type)

        # populate dims vars
        for var in dim.vars:
            pca_comp_brick.dims[0].add_var(
                var.type_term, var.units_term, var.values, var.scalar_type)

        pca_comp_brick.dims[1].add_var(self.brick_dim_var_type_term, None, [
            'PCA%s' % (i + 1) for i in range(self.n_components)])

        b_prov = self.__brick.get_base_session_provenance()
        prov = BrickProvenance('sklearn.decomposition.PCA',
                               ['n_components:%s' % self.n_components,
                                'dim_index:%s' % 1])
        b_prov.provenance_items.append(prov)
        pca_comp_brick.session_provenance.provenance_items.append(b_prov)
        return pca_comp_brick

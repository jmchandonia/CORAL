export interface MicroTypeTree {
    rootNodes: MicroTypeTreeNode[];
}

export interface MicroTypeTreeNode {
    mt_data_var: boolean,
    mt_dim_var: boolean,
    mt_dimension: boolean,
    mt_microtype: boolean,
    mt_parent_term_ids: string[],
    mt_property: boolean,
    mt_valid_units: string,
    mt_valid_values:  string,
    mt_value_scalar_type: string,
    term_def: string,
    term_desc: string,
    term_id: string,
    term_name: string,
    children?: MicroTypeTreeNode[]
}
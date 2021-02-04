import { Node, ClusterOptions } from 'vis-network/standalone';

export interface HomepageNode extends Node {

    /* 
    Extension interface to provide metadata to nodes to 
    enable search and interaction with generix system. This
    is a wrapper for the VisJS Node interface that will allow
    us to use nodes with a 'data' property without throwing
    a type error.
     */

    data: INodeData;
    cid?: number;
}

export interface INodeData {

    /* JSON data structure for nodes from request to /types_graph */

    index: number;
    name: string;
    category: string | false;
    dataType: string;
    dataModel: string;
    thickness: number;
    isParent: boolean;
    x: number;
    y: number;
    root?: true;
    count: number;
    parent?: number;
}

export class HomepageNodeFactory {
    public static createNode(data: INodeData, xScale: number, yScale: number): HomepageNode {
        const node: HomepageNode = {
            data,
            id: data.index,
            font: {
                size: 16,
                face: 'Red Hat Text, sans-serif',
            },
            color: {
                background: data.category ? 'white' : 'rgba(0,0,0,0)', // make node invisible when its a connector
                border: data.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
                hover: { background: '#ddd' }
            },
            shape: 'box',
            shapeProperties: {
                borderRadius: data.category === 'DDT_' ? 0 : 20
            },
            fixed: true,
            x: data.x * xScale,
            y: data.y * yScale
        }

        if (data.root) {
            node.borderWidth = 4;
            node.color = {
                border: 'darkgreen',
                hover: { background: '#ddd' },
                background: 'white'
            }
            node.margin = {
                top: 10,
                left: 10,
                bottom: 10,
                right: 10
            };
        } else if (!data.category) {
            node.borderWidth = 0;
        }

        if (data.category) {
            node.label = `${data.count} ${data.name.replace(/<br>/g, '\n')}`;
        }

        if (data.parent) {
            node.cid = data.parent;
        }

        if (data.isParent) {
            node.label = '[-]'; // parent displays as expanded root node in cluster
        }

        return node;
    }

    public static createNodeCluster(data: INodeData, xScale: number, yScale: number): ClusterOptions {
        return {
            joinCondition: node => (node.cid && node.cid === data.index) || node.id === data.index,
            clusterNodeProperties: {
                label: `${data.count} ${data.name} [+]`,
                physics: false,
                color: {
                    border: data.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
                    background: 'white'
                },
                borderWidth: 3,
                shape: 'box',
                shapeProperties: {
                    borderRadius: 0
                },
                x: data.x * xScale,
                y: data.y * yScale,
                font: {
                    size: 16,
                    face: 'Red Hat Text, sans-serif'
                },
            },
        }
    }
}

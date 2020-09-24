import { Edge } from 'vis-network/standalone';
import { HomepageNode } from './homepage-node';

export interface IEdgeData {

    /* JSON Edge structure from response to /types_graph */

    thickness: number;
    text: string;
    source: number;
    target: number;
    in_filter: boolean; // determines if process matched in search filter
    reversible: boolean; // a 2 way relationship between types, needs different curvature so edges arent on top of eachother
}

export class HomepageEdgeFactory {
    public static createEdge(data: IEdgeData, targetNode: HomepageNode, toId?: number, fromId?: number): Edge {
        return {
            from: targetNode.cid ? targetNode.cid : data.source,
            to: data.target,
            width: data.thickness,
            physics: false,
            label: data.text.replace(/<br>/g, '\n').replace(/&rarr;/g, ' → '),
            color: data.in_filter ? 'blue' : '#777',
            selfReference: {
                angle: 0.22 // size of edges for nodes pointing at themselves
            },
            font: {
                size: 16,
                // hide labels until they are hovered over
                color: 'rgba(0,0,0,0)',
                strokeColor:  'rgba(0,0,0,0)'
            },
            arrows: {
                to: {
                    // hide arrows for 'connector' nodes
                    enabled: targetNode && targetNode.data.category !== false
                }
            },
            smooth: {
                enabled: data.reversible === true,
                roundness: 0.2,
                forceDirection: 'vertical',
                type: 'curvedCW',
            },
        }
    }
}
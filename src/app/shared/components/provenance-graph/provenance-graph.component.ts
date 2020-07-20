import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
// import * as d3 from 'd3';
// import * as vis from 'vis-network';
import { Network, DataSet } from 'vis';
import { ValueTransformer } from '@angular/compiler/src/util';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');

@Component({
  selector: 'app-provenance-graph',
  templateUrl: './provenance-graph.component.html',
  styleUrls: ['./provenance-graph.component.css']
})
export class ProvenanceGraphComponent implements OnInit, AfterViewInit {

  nodes: { id: number, label: string, data: any }[];
  edges: { from: number, to: number }[];

  @ViewChild('pGraph') pGraph: ElementRef;

  options = {
    physics: {
      // enabled: false,
      hierarchicalRepulsion: {
        // avoidOverlap: 1
        // nodeDistance: 200
      }
    },
    layout: {
      hierarchical: {
        direction: 'UD',
        sortMethod: 'hubsize',
        nodeSpacing: 200,
        levelSeparation: 75
        // shakeTowards: 'leaves'
      }
    },
    edges: {
      arrows: {
        to: {
          enabled: true,
        }
      },
      font: {
        size: 0,
      }
    }
  };

  network: any; // TODO: see if there is @types/vis-network

  constructor(
  ) { }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    this.nodes = new DataSet(
      mockData.result.nodes.map(this.createNode)
    );

    this.edges = new DataSet(
      // mockData.result.links.map(edge => ({from: edge.source, to: edge.target}))
      mockData.result.links.map(this.createEdge)
    );

    this.network = new Network(
      this.pGraph.nativeElement,
      {
        nodes: this.nodes,
        edges: this.edges
      },
      this.options
    );
 }

 createNode(dataItem: any) {
  const node: any = {
    id: dataItem.index,
    label: dataItem.type !== 'null' ? `${dataItem.count} ${dataItem.name}` : '',
    // color: node.type === 'dynamic' ? 'blue' : 'red',
    color: {
      background: dataItem.type !== 'null' ? 'white' : 'rgba(0,0,0,0)',
      border: dataItem.type === 'dynamic' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
      hover: { background: '#ddd' }
    },
    borderWidth: dataItem.type === 'null' ? 0 : 1,
    // opacity: dataItem.type === 'null' ? 0 : 1,
    // physics: 'false',
    physics: false,
    shape: 'box',
  }
  return node;
 }

 createEdge(edgeItem: any) {
   return {
     from: edgeItem.source,
     to: edgeItem.target,
     label: 'label',
     chosen: {
        edge: (values) => {
          values.size = 14;
        } 
     }
   }
 }

}

import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { Network, DataSet } from 'vis';
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
    interaction: {
      zoomView: false,
      dragView: false,
      hover: true
    },
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
        levelSeparation: 75,
      }
    },
    edges: {
      arrows: {
        to: {
          enabled: true,
        }
      },
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
    
    // set zoom level to contain all nodes
    this.network.fit({
      nodes: this.nodes.map(node => node.id),
      animation: true
    });
 }

 createNode(dataItem: any) {
  const node: any = {
    id: dataItem.index,
    label: dataItem.type !== 'null' ? `${dataItem.count} ${dataItem.name}` : '',
    font: {
      size: 16
    },
    color: {
      background: dataItem.type !== 'null' ? 'white' : 'rgba(0,0,0,0)',
      border: dataItem.type === 'dynamic' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
      hover: { background: '#ddd' }
    },
    borderWidth: dataItem.type === 'null' ? 0 : 1,
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
     font: {
       size: 16,
       color: 'rgba(0,0,0,0)',
       strokeColor: 'rgba(0,0,0,0)'
     },
     chosen: {
      edge: (values, id, selected, hovering) => {
        values.width = 2;
      },
      label: (values, id, selected, hovering) => {
        // make label visible on edge click
        values.color = 'black';
        values.strokeColor = 'white';
      },
    }
   }
 }

}

import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
// import * as d3 from 'd3';
// import * as vis from 'vis-network';
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

  options = { physics: false };

  network: any; // TODO: see if there is @types/vis-network

  constructor(
  ) { }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    this.nodes = new DataSet(
      mockData.result.nodes.map(node => {
        // {id: node.index, label: `${node.count} ${node.name}`}
        return {
          id: node.index,
          label: `${node.count} ${node.name}`,
          // color: node.type === 'dynamic' ? 'blue' : 'red',
          color: {
            background: 'white',
            border: node.type === 'dynamic' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
            hover: { background: '#ddd' }
          },
          // opacity: node.type === 'null' ? 0 : 1 
          shape: 'box'
        }
      })
    );

    this.edges = new DataSet(
      mockData.result.links.map(edge => ({from: edge.source, to: edge.target}))
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

}

import { Component, OnInit, ElementRef, ViewChild, AfterViewInit, EventEmitter, Output } from '@angular/core';
import { Network, DataSet, Node, Edge } from 'vis-network/standalone';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');
import { QueryMatch } from 'src/app/shared/models/QueryBuilder';
import { partition } from 'lodash';

@Component({
  selector: 'app-provenance-graph',
  templateUrl: './provenance-graph.component.html',
  styleUrls: ['./provenance-graph.component.css']
})
export class ProvenanceGraphComponent implements OnInit, AfterViewInit {

  nodes:  DataSet<any>;
  edges: DataSet<any>;
  @Output() querySelected: EventEmitter<QueryMatch> = new EventEmitter();

  @ViewChild('pGraph') pGraph: ElementRef;

  options = {
    interaction: {
      zoomView: false,
      dragView: false,
      hover: true
    },
    layout: {
      improvedLayout: true,
      hierarchical: {
        direction: 'UD',
        sortMethod: 'hubsize',
        nodeSpacing: 200,
        levelSeparation: 75,
        // blockShifting: true,
        // edgeMinimization: true
        // parentCentralization: true,
        // shakeTowards: 'leaves'
      }
    }
  };

  coreTypeNodes: any[];
  dynamicTypeNodes: any[];

  network: Network;

  constructor(
  ) { }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {

    const [coreTypes, dynamicTypes] = partition(mockData.result.nodes, node => node.category !== 'DDT_')

    console.log('tyoe', coreTypes.length, dynamicTypes.length);

    this.nodes = new DataSet(
      // mockData.result.nodes.map(this.createNode)
      coreTypes.map(this.createNode)
    );

    dynamicTypes.forEach(dynamicType => this.nodes.update(this.createNode(dynamicType)));

    this.edges = new DataSet(
      mockData.result.links.map(edge => this.createEdge(edge.source, edge.target))
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

    // add double click event listener to submit search query on nodes
    this.network.on('doubleClick', ({nodes}) => this.submitSearchQuery(nodes));

    // click will toggle expand child nodes
    this.network.on('click', ({nodes}) => this.toggleExpandNodes(nodes));
 }

  createNode(dataItem: any): Node {
    const node: any = {
      id: dataItem.index,
      label: dataItem.category !== 'null' ? `${dataItem.count} ${dataItem.name}` : '',
      font: {
        size: 16
      },
      color: {
        background: dataItem.category !== 'null' ? 'white' : 'rgba(0,0,0,0)',
        border: dataItem.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
        hover: { background: '#ddd' }
      },
      borderWidth: dataItem.category === 'null' ? 0 : 1,
      physics: false,
      shape: 'box',
      data: {...dataItem},
      chosen: {},
    }

    if (dataItem.children) {
      node.data.childrenExpanded = false;
      node.label += ' [+]';
    }

    return node;
  }

  createEdge(fromId?: number | string, toId?: number | string): any {
    // const target = this.nodes.get(edgeItem.target);
    const target = this.nodes.get(toId);
    return {
      from: fromId,
      to: toId,
      label: 'label',
      font: {
        // hide labels initially
        size: 16,
        color: 'rgba(0,0,0,0)',
        strokeColor: 'rgba(0,0,0,0)'
      },
      arrows: {
        to: {
          // hide arrows for 'connector' nodes
          enabled: target && target.data.category !== 'null'
        }
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

  submitSearchQuery(nodes) {
    if (nodes.length) {
      const { category, dataType, dataModel } = this.nodes.get(nodes)[0].data;
      const query = new QueryMatch({category, dataType, dataModel});
      this.querySelected.emit(query);
    }
  }

  toggleExpandNodes(nodes) {
    // only run if a node is clicked
    if (nodes.length) {
      const node = this.nodes.get(nodes)[0]
      // only run if node has children
      if (node.data.children) {
        if (!node.data.childrenExpanded) {
          // expand hidden nodes
          node.data.children.forEach(child => {
            this.nodes.update(this.createNode(child));
            this.edges.update(this.createEdge(node.id, child.index))
          });
          node.data.childrenExpanded = true;
        } else {
          // hide expanded nodes
          this.nodes.remove(node.data.children.map(child => child.index));
          node.data.childrenExpanded = false;
        }
        this.network.fit(
          {animation: true}
        );
      }
    }
  }

}

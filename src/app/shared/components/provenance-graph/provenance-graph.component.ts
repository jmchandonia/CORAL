import { Component, OnInit, ElementRef, ViewChild, EventEmitter, Output, OnDestroy } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { Network, DataSet, Node, Edge, NodeChosen } from 'vis-network/standalone';
import { QueryMatch, Process } from 'src/app/shared/models/QueryBuilder';
import { partition } from 'lodash';
import { HomeService } from 'src/app/shared/services/home.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-provenance-graph',
  templateUrl: './provenance-graph.component.html',
  styleUrls: ['./provenance-graph.component.css']
})
export class ProvenanceGraphComponent implements OnInit, OnDestroy {

  nodes:  DataSet<any>;
  edges: DataSet<any>;
  clusterNodes: any[] = []; // TODO: make models for response JSON
  @Output() querySelected: EventEmitter<{query: QueryMatch, processes: Process}> = new EventEmitter();

  provenanceLoadingSub: Subscription;
  provenanceGraphSub: Subscription;
  noResults = false;

  @ViewChild('pGraph') pGraph: ElementRef;

  options = {
    interaction: {
      zoomView: false,
      dragView: false,
      hover: true
    },
    physics: false,
    layout: {
      randomSeed: '0:0'
    }
  };

  coreTypeNodes: any[];
  dynamicTypeNodes: any[];

  network: Network;
  xScale: number;
  yScale: number;

  height: number;
  width: number;

  constructor(
    private homeService: HomeService,
    private spinner: NgxSpinnerService,
  ) { }

  ngOnInit(): void {
    this.spinner.show('pgraph-loading');
    this.provenanceLoadingSub = this.homeService.getProvenanceLoadingSub()
    .subscribe(() => {
      this.noResults = false;
      this.network.destroy();
      this.spinner.show('pgraph-loading');
    });
    this.provenanceGraphSub = this.homeService.getProvenanceGraphSub()
      .subscribe((data: any) => {
        this.spinner.hide('pgraph-loading');
        this.initNetworkGraph(data.results);
      });
  }

  calculateScale(nodes) {
    const {scrollHeight, scrollWidth} = this.pGraph.nativeElement.parentElement;
    const xSort = nodes.map(d => d.x).sort((a, b) => a - b),
    ySort = nodes.map(d => d.y).sort((a, b) => a - b);

    const xRange = xSort.pop() - xSort[0];
    const yRange = ySort.pop() - ySort[0];

    this.xScale = scrollWidth / xRange
    this.yScale = scrollHeight / yRange;
  }

  ngOnDestroy() {
    if (this.provenanceLoadingSub) {
      this.provenanceLoadingSub.unsubscribe();
    }
    if (this.provenanceGraphSub) {
      this.provenanceGraphSub.unsubscribe();
    }
  }

  initNetworkGraph(data) {
    this.calculateScale(data.nodes);
    const [coreTypes, dynamicTypes] = partition(data.nodes, node => node.category !== 'DDT_');

    if (!coreTypes.length && !dynamicTypes.length) {
      this.noResults = true;
      return;
    }
    // initialize core type nodes with x y coordinates
    this.nodes = new DataSet(coreTypes.map(node => this.createNode(node)));

    // layout dynamic types with visJS physics engine
    dynamicTypes.forEach(dynamicType => {
      if (dynamicType.isParent) {
        this.clusterNodes.push({
          ...dynamicType, extended: true,
        });
      }
      this.nodes.update(this.createNode(dynamicType));
    });

    // initialize edges
    this.edges = new DataSet(
      data.links.map(edge => this.createEdge(edge))
    );

    // render network
    this.network = new Network(
      this.pGraph.nativeElement,
      {
        nodes: this.nodes,
        edges: this.edges
      },
      this.options
    );

    // cluster nodes from clusterNodes array
    this.clusterNodes.forEach(clusterNode => this.addCluster(clusterNode));

    // set zoom level to contain all nodes
    this.network.fit({
      nodes: this.nodes.map(node => node.id),
      animation: false
    });

    // add double click event listener to submit search query on nodes
    this.network.on('doubleClick', ({nodes}) => this.submitSearchQuery(nodes));

    // add click event to expand cluster nodes
    this.network.on('click', ({nodes}) => {
      const clusteredNode = this.clusterNodes.find(node => node.index === nodes[0]);
      if(clusteredNode && clusteredNode.expanded) {
        this.reclusterNode(nodes[0]);
      }
    });

    // show edge labels on hover
    this.network.on('hoverEdge', ({edge}) => {
      this.network.updateEdge(edge, {font: {color: 'black', strokeColor: 'white'}}); // vadjust
    });

    // hide edge labels on hover leave 
    this.network.on('blurEdge', ({edge}) => {
      this.network.updateEdge(edge, {font: {color: 'rgba(0,0,0,0)', strokeColor: 'rgba(0,0,0,0)'}});
    });

    // disable physics after nodes without coordinates have been pushed apart
    this.network.stabilize();

    this.network.on('stabilizationIterationsDone', () => {
      this.nodes.forEach(node => {
        this.nodes.update({id: node.id, fixed: false});
      });
    });

  }

 addCluster(data) {
   // configuration for nodes that hold clusters together
   this.network.cluster({
    // joinCondition: node => (node.cid && node.cid === data.index) || node.id === data.index,
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
      x: data.x,
      y: data.y,
      font: {
        size: 16,
        face: 'Red Hat Text, sans-serif'
      },
      chosen: {
        node: (values, id, selected, hovering) => {
          if (selected) {
            data.expanded = true;
            this.network.openCluster(id, {
              // function to move child nodes to their specified position
              releaseFunction: (_, positions) => positions 
            });
          }
        },
        label: (values, id, selected) => {
          if(selected) { values.size = 0; }
        }
      } as NodeChosen
    },
   });
 }

 reclusterNode(nodeID) {
   const cluster = this.clusterNodes.find(item => item.index === nodeID);
   this.addCluster(cluster);
 }

  createNode(dataItem: any): Node {
    const node: any = {
      id: dataItem.index,
      font: {
        size: 16,
        face: 'Red Hat Text, sans-serif'
      },
      color: {
        background: dataItem.category !== false ? 'white' : 'rgba(0,0,0,0)',
        border: dataItem.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
        hover: { background: '#ddd' }
      },
      cid: dataItem.cid,
      shape: 'box',
      shapeProperties: {
        borderRadius: dataItem.category === 'DDT_' ? 0 : 20
      },
      data: {...dataItem},
      fixed: true,

      x: dataItem.x,
      y: dataItem.y
    } 

    if (dataItem.root) {
      node.borderWidth = 4;
      node.margin = 10;
      node.color.border = 'darkgreen';
    } else if (!dataItem.category) {
      node.borderWidth = 0;
    }

    if (dataItem.category) {
      node.label = `${dataItem.count} ${dataItem.name.replace(/<br>/g, '\n')}`;
    }

    if(dataItem.parent) {
      node.cid = dataItem.parent;
    }

    if (dataItem.children?.length) {
      node.label = '[-]';
    }

    if(dataItem.category === 'SDT_') { node.mass = 10; }

    return node;
  }

  createEdge(edge): any {
    const toId = edge.target;
    const fromId = edge.source;
    const target: any = this.nodes.get(toId);
    return {
      from: target.cid ? target.cid : fromId,
      to: toId,
      width: edge.thickness,
      label: edge.text.replace(/<br>/g, '\n').replace(/&rarr;/g, ' → '), // TODO: implement safeHtmlParser
      color: edge.in_filter ? 'blue' : '#777',
      physics: true,
      selfReference: {
        angle: 0.22
      },
      font: {
        // hide labels initially
        size: 16,
        color: 'rgba(0,0,0,0)',
        strokeColor: 'rgba(0,0,0,0)',
      },
      arrows: {
        to: {
          // hide arrows for 'connector' nodes
          enabled: target && target.data.category !== false
        }
      },
      smooth: {
        enabled: edge.reversible === true,
        roundness: 0.2,
        forceDirection: 'vertical',
        type: 'curvedCW'
      },
    }
 }

  submitSearchQuery(nodes) {
    if (nodes.length) {
      const node = this.nodes.get(nodes)[0]
      const { category, dataType, dataModel } = node.data;
      const edgeIds = this.network.getConnectedEdges(node.id);
      const processes: Process[] = category === 'DDT_' ? this.getInputProcesses(edgeIds, node.id) : [];
      const query = new QueryMatch({category, dataType, dataModel});
      this.querySelected.emit({query, processes: processes[0]}); // TODO: reduce to 1 item
    }
  }

  getInputProcesses(edgeIds, targetId): Process[] {
    return edgeIds
      .map(id => this.edges.get(id)) // get edge data from array of ids
      .filter(edge => edge && edge.to === targetId) // we only want parent edges and not children
      .map(edge => {
        // TODO: interface NodeWithData extends Node so you don't have to keep explicitly typing nodes as 'any'
        const sourceNode: any = this.nodes.get(edge.from);
        if (!sourceNode.data.category) {
          // get source and multiple targets if source is a 'connector' node
          const [sourceEdges, targetEdges] = partition(
            this.network.getConnectedEdges(sourceNode.id).map(id => this.edges.get(id)),
            edge => edge.to === sourceNode.id
          );
          return new Process(
            sourceEdges.map(edge => {
              const sourceNode = (this.nodes.get(edge.from) as any);
              if (sourceNode.data.children) {
                // if there is children then we need to grab the next parent node, the current node is only for UI
                const nextSourceEdge = this.network
                  .getConnectedEdges(sourceNode.id)
                  .map(id => this.edges.get(id))
                  .filter(edge => edge.to === sourceNode.id)[0];
                const nextSourceNode = this.nodes.get(nextSourceEdge.from) as any;
                return `${nextSourceNode.data.category}${nextSourceNode.data.dataType}`;
              }
              return `${sourceNode.data.category}${sourceNode.data.dataType}`;
            }),
            targetEdges.map(edge => {
              const targetNodeData = (this.nodes.get(edge.to) as any).data;
              return `${targetNodeData.category}${targetNodeData.dataType}`;
            })
          );
        } else {
          const { dataType, category } = sourceNode.data;
          const targetNodeData = (this.nodes.get(targetId) as any).data;
          return new Process(
            [category + dataType],
            [targetNodeData.category + targetNodeData.dataType]
          );
        }
      });
  }

}

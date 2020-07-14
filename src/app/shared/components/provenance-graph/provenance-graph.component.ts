import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
const prov = require('src/app/shared/test/mock-provenance-graph.json').result;
import * as d3 from 'd3';

@Component({
  selector: 'app-provenance-graph',
  templateUrl: './provenance-graph.component.html',
  styleUrls: ['./provenance-graph.component.css']
})
export class ProvenanceGraphComponent implements OnInit, AfterViewInit {

  margin = {top: 1, right: 1, bottom: 6, left: 1};

  width = 600;
  height = 900;

  @ViewChild('provenanceGraph') pGraph: ElementRef;
  svg: any;
  // svg: d3.Selection<SVGElement>;
  path: any;

  constructor() { }

  ngOnInit(): void {
  }

  ngAfterViewInit() {
        const simulation = d3.forceSimulation(prov.nodes)
          .force('charge', d3.forceManyBody().strength(-100))
          .force('center', d3.forceCenter(this.width / 2, this.height / 2))
          .force('link', d3.forceLink().links(prov.links))
          .on('tick', ticked);

          function ticked() {
            updateLinks();
            updateNodes();
          }

          function updateLinks() {
            var u: any = d3.select('.links')
              .selectAll('line')
              .data(prov.links);

            u.enter()
              .append('line')
              .merge(u)
              .attr('x1', function(d) { return d.source.x })
              .attr('y1', function(d) { return d.source.y })
              .attr('x2', function(d) { return d.target.x })
              .attr('y2', function(d) { return d.target.y })
              .attr('stroke', 'black');

            u.exit().remove();
          }

          function updateNodes() {
            const v: any = d3.select('.nodes')
              .selectAll('text')
              .data(prov.nodes)

            v.enter()
              // .append('circle')
              // .attr('r', 50)
              // .attr('cx', function(d) { return d.x })
              // .attr('cy', function(d) { return d.y })
              // .attr('fill', "#CED4DA")
              .append('text')
              .text(function(d) { return d.count + ' ' + d.name })
              .merge(v)
              .attr('x', function(d) { return d.x })
              .attr('y', function(d) { return d.y })
              .attr('dy', function(d) { return 5 })

              v.exit().remove();
          }

        // simulation.force('link',
        //   d3.forceLink()
        //     .distance(5)
        //     .strength(2)
        // );

      // });
  }
}

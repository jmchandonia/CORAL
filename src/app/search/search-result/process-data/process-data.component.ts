import { Component, OnInit, Input, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';

@Component({
  selector: 'app-process-data',
  templateUrl: './process-data.component.html',
  styleUrls: ['./process-data.component.css']
})
export class ProcessDataComponent implements OnInit, AfterViewInit {

  processesDown = [
    {
      name: 'process1',
      outputs: [
        {
          dataType: 'Gene Knockout Fitness',
          category: '_DDT',
          name: 'TnSeq1',
          id: 'tnseq0000003'
        },
        {
          dataType: 'TnSeqLibrary',
          category: '_SDT',
          name: 'TnSeq1',
          id: 'tnseq0000003'
        },
        {
          dataType: 'Physical Measurement',
          category: '_DDT',
          name: 'TnSeq1',
          id: 'tnseq0000003'
        }
      ]
    },
    {
      name: 'process2',
      outputs: [
        {
          dataType: 'Read',
          category: '_SDT',
          name: 'TnSeq1',
          id: 'tnseq0000003'
        },
        {
          dataType: 'Chemical Measurement',
          category: '_DDT',
          name: 'TnSeq1',
          id: 'tnseq0000003'
        }
      ]
    },
    {
      name: 'process3',
      outputs: [
        {
          dataType: 'TnSeqLibrary',
          category: '_DDT',
          name: 'TnSeq1',
          id: 'tnseq0000003'
        }
      ]
    }
  ];

  dataTables: any;

  constructor(private router: Router, private chRef: ChangeDetectorRef) { }

  @Input() id: string;

  ngAfterViewInit() {
    const tables: any = $('.process-table');
    console.log('TABLES', tables);
    this.dataTables = tables.DataTable({
      ordering: false,
      info: false
    });
    this.chRef.detectChanges();
  }

  ngOnInit() {}

  navigate(output) {
    this.router.navigate(
      output.category === '_DDT'
        ? [`search/result/${output.id}`]
        : [`search/result/core-type/${output.id}`]
    );
  }

}

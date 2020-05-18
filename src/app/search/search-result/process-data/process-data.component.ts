import { Component, OnInit, Input, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';

@Component({
  selector: 'app-process-data',
  templateUrl: './process-data.component.html',
  styleUrls: ['./process-data.component.css']
})
export class ProcessDataComponent implements OnInit, AfterViewInit {

  processesDown: any[];
  processesUp: any[];
  hideProcessUp = false;
  hideProcessDown = false;
  hideProcessInputs = true;
  hideProcessOutputs: boolean[] = [];
  dataTables: any;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private chRef: ChangeDetectorRef,
    private queryBuilder: QueryBuilderService
    ) { }

  @Input() id: string;
  @Input() item: any;

  ngAfterViewInit() {
    const tables: any = $('.data-table');
    this.dataTables = tables.DataTable({
      ordering: false,
      info: false
    });
    this.chRef.detectChanges();
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params.id) {
        this.id = params.id;
        this.getProcesses();
      }
    });
  }

  getProcesses() {
    this.queryBuilder.getProcessesUp(this.id)
    .subscribe((data: any) => {
      this.processesUp = data.results;
    });
    this.queryBuilder.getProcessesDown(this.id)
    .subscribe((data: any) => {
      this.processesDown = data.results;
      this.hideProcessOutputs = [...this.processesDown.map(() => true)];
    });
  }

  toggleProcessOutputs(index) {
    this.hideProcessOutputs[index] = !this.hideProcessOutputs[index];
  }

  navigate(output) {
    const route = output.category === 'DDT_'
      ? `/search/result/brick/${output.id}`
      : `/search/result/core/${output.id}`;
    this.router.navigate([route]);
  }

  objectKeys(n) {
    return Object.keys(n).filter(o => n[o] !== null);
  }

}

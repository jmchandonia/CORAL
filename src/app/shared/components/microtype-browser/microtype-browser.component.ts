import { Component, OnInit, ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { UploadService } from '../../services/upload.service';
import * as $ from 'jquery';
import 'datatables.net-bs4';
import 'datatables.net';
import { NgxSpinnerService } from 'ngx-spinner';
import { MicrotypeTreeService } from 'src/app/shared/services/microtype-tree.service';
import { MicroTypeTreeNode } from 'src/app/shared/models/microtype-tree';
import { ITreeOptions, TreeComponent, TreeModel } from 'angular-tree-component'

@Component({
  selector: 'app-microtype-browser',
  templateUrl: './microtype-browser.component.html',
  styleUrls: ['./microtype-browser.component.css']
})
export class MicrotypeBrowserComponent implements OnInit {

  public microtypes: MicroTypeTreeNode[];
  dataTables: any;
  public treeOptions: ITreeOptions = { displayField: 'term_def' }
  @ViewChild('tree', {static: false}) tree: TreeComponent;

  constructor(
    private uploadService: UploadService,
    private chRef: ChangeDetectorRef,
    private spinner: NgxSpinnerService,
    private treeService: MicrotypeTreeService
  ) { }

  ngOnInit() {
    this.treeService.getMicrotypes()
      .then((microtypes: MicroTypeTreeNode[]) => {
        this.microtypes = microtypes;
        this.chRef.detectChanges();
      });
  }

  getMicrotypeMetadata(event) {
    console.log('getting microtype metadata', event.node.data);
  }

  setKeywordSearchFilter(event) {
    this.tree.treeModel.filterNodes(event.target.value);
  }

}

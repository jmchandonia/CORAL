import { Component, OnInit, Input } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-load-success-table',
  templateUrl: './load-success-table.component.html',
  styleUrls: ['./load-success-table.component.css']
})
export class LoadSuccessTableComponent implements OnInit {

  @Input() data: any;
  brick: Brick;

  constructor(
    private uploadService: UploadService
  ) { }


  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
  }

}

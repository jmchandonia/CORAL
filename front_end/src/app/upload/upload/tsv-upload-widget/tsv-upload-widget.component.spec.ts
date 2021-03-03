import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TSVUploadWidgetComponent } from './tsv-upload-widget.component';

describe('TSVUploadWidgetComponent', () => {
  let component: TSVUploadWidgetComponent;
  let fixture: ComponentFixture<TSVUploadWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TSVUploadWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TSVUploadWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
